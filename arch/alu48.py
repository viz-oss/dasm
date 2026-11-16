"""Architecture backend for the 4-bit ALU instruction format.

The ALU is not a general-purpose CPU.  It emits one byte per instruction:

    [7:5] opcode | [4:1] A | [0] carry-in override

The second ALU input is supplied by the hardware and is therefore not encoded.

Format slowa instrukcji (8 bit):

```
[7:5] opcode (3 bity)
[4:1] operand A (4 bity, 0-15)
[0]   Cn override (0/1, opcjonalny)
```

Mnemoniki: `ADD, SUB, AND, OR, XOR, NOT, SHL, SHR`

```asm
ADD 5        ; A=5, Cn=0
ADD 5, 1     ; A=5, Cn=1
SUB 10
AND 0b1010   ; operandy: dec, 0x.. (hex), 0b.. (bin)
SHR 8
```

Tryb `--microcode` generuje tabele do zaprogramowania EEPROM dekodera
opcode -> sygnaly 74181 (S3 S2 S1 S0, M, Cn) + bit “external shift enable” dla SHR.
Adres EEPROM = 3-bit opcode, dane = 7 bitow.
"""

from arch.base import Architecture


class Alu4Architecture(Architecture):
    """Backend for the 4-bit ALU and its 8-bit control words."""

    word_size = 1
    endian = "little"
    entry_jump_size = 0

    OPCODES = {
        "ADD": {"opcode": 0b000, "S": 0b1001, "M": 0, "Cn": 0},
        "SUB": {"opcode": 0b001, "S": 0b0110, "M": 0, "Cn": 1},
        "AND": {"opcode": 0b010, "S": 0b1011, "M": 1, "Cn": None},
        "OR": {"opcode": 0b011, "S": 0b1110, "M": 1, "Cn": None},
        "XOR": {"opcode": 0b100, "S": 0b0110, "M": 1, "Cn": None},
        "NOT": {"opcode": 0b101, "S": 0b0000, "M": 1, "Cn": None},
        "SHL": {"opcode": 0b110, "S": 0b0000, "M": 0, "Cn": 1},
        "SHR": {"opcode": 0b111, "S": None, "M": None, "Cn": None},
    }

    def instruction_set(self) -> dict:
        """Return the ALU mnemonic description."""
        return {
            mnemonic: {
                "opcode": info["opcode"],
                "opcode_bits": 3,
                "operands": ["imm4", "imm1"],
            }
            for mnemonic, info in self.OPCODES.items()
        }

    @staticmethod
    def _parse_operand(token: str, labels: dict[str, int]) -> int:
        token = token.strip()
        if token in labels:
            return labels[token]
        return int(token, 0)

    def encode(self, mnemonic: str, operands: list[str], context: dict | None = None) -> int:
        """Encode one ALU instruction as an 8-bit control word."""
        mnemonic = mnemonic.upper()
        if mnemonic not in self.OPCODES:
            raise ValueError(f"Unknown instruction: {mnemonic}")
        if not 1 <= len(operands) <= 2:
            raise ValueError(f"{mnemonic} requires operand A and accepts optional Cn")

        context = context or {}
        labels = context.get("labels", {})
        a_value = self._parse_operand(operands[0], labels)
        if not 0 <= a_value <= 0xF:
            raise ValueError(f"Operand A out of range 0..15: {a_value}")

        carry = 0
        if len(operands) == 2:
            carry = self._parse_operand(operands[1], labels)
            if carry not in (0, 1):
                raise ValueError("Cn override must be 0 or 1")

        return (self.OPCODES[mnemonic]["opcode"] << 5) | (a_value << 1) | carry

    def microcode_table(self) -> list[dict]:
        """Return EEPROM data for opcode-to-74181 control decoding."""
        table = []
        for mnemonic, info in sorted(
            self.OPCODES.items(), key=lambda item: item[1]["opcode"]
        ):
            if mnemonic == "SHR":
                data = 0b0000001
            else:
                carry = info["Cn"] if info["Cn"] is not None else 0
                data = (info["S"] << 3) | (info["M"] << 2) | (carry << 1)

            table.append({
                "opcode": info["opcode"],
                "mnemonic": mnemonic,
                "data_bin": format(data, "07b"),
                "data_hex": format(data, "02X"),
            })
        return table

    def mov(self, instr) -> list[int]:
        raise NotImplementedError(
            "The ALU backend has no generic MOV instruction; use encode()"
        )

    def call(self, instr, offset: int = 0) -> list[int]:
        raise NotImplementedError("The ALU backend has no CALL instruction")

    def ret(self, instr) -> list[int]:
        raise NotImplementedError("The ALU backend has no RETURN instruction")

    def exit(self, instr) -> list[int]:
        raise NotImplementedError("The ALU backend has no EXIT instruction")

    def jmp(self, target: str, offset: int = 0) -> list[int]:
        raise NotImplementedError("The ALU backend has no JMP instruction")


EXPORTS = Alu4Architecture
