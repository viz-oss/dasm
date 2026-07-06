"""
Modul architektury: alu4
4-bitowe ALU, 8 operacji (3-bit opcode), bez etykiet/skokow (samo ALU, nie CPU).

Format slowa instrukcji (8 bitow):

  bit:  7 6 5 | 4 3 2 1 | 0
        OPCODE| A (4b)  | (rezerwa / Cn override)

Layout:
  [7:5] opcode (3 bity)
  [4:1] operand A - 4-bit wartosc testowa wpisywana do rejestru A
  [0]   Cn override (carry-in dla SUB/ADD), domyslnie 0

Operand B wpisywany jest osobno (sprzetowo, np. przelacznikami) - nie jest
czescia slowa instrukcji w tej minimalnej wersji.

Mnemoniki i kodowanie opcode -> sygnaly 74181 (S3 S2 S1 S0, M, Cn) - patrz README.
"""

from architectures.base import Architecture


class Alu4Architecture(Architecture):

    name = "alu4"
    word_size = 8
    supports_labels = False

    # opcode -> (binarna wartosc opcode, sygnaly sterujace 74181: S3S2S1S0, M, Cn)
    OPCODES = {
        "ADD": {"opcode": 0b000, "S": 0b1001, "M": 0, "Cn": 0},
        "SUB": {"opcode": 0b001, "S": 0b0110, "M": 0, "Cn": 1},
        "AND": {"opcode": 0b010, "S": 0b1011, "M": 1, "Cn": None},
        "OR":  {"opcode": 0b011, "S": 0b1110, "M": 1, "Cn": None},
        "XOR": {"opcode": 0b100, "S": 0b0110, "M": 1, "Cn": None},
        "NOT": {"opcode": 0b101, "S": 0b0000, "M": 1, "Cn": None},
        "SHL": {"opcode": 0b110, "S": 0b0000, "M": 0, "Cn": 1},
        "SHR": {"opcode": 0b111, "S": None,   "M": None, "Cn": None},  # logika zewnetrzna
    }

    def instruction_set(self) -> dict:
        result = {}
        for mnemonic in self.OPCODES:
            result[mnemonic] = {
                "opcode": self.OPCODES[mnemonic]["opcode"],
                "opcode_bits": 3,
                "operands": ["imm4"],  # wartosc A; Cn override mozna podac jako drugi opcjonalny operand
            }
        return result

    def encode(self, mnemonic: str, operands: list[str], context: dict) -> int:
        mnemonic = mnemonic.upper()
        if mnemonic not in self.OPCODES:
            raise ValueError(f"Nieznana instrukcja: {mnemonic}")

        info = self.OPCODES[mnemonic]
        opcode = info["opcode"]

        if len(operands) < 1:
            raise ValueError(f"{mnemonic} wymaga operandu A (0-15)")

        a_value = self.parse_operand(operands[0], "imm4", context.get("labels", {}))
        if not (0 <= a_value <= 0xF):
            raise ValueError(f"Operand A poza zakresem 0-15: {a_value}")

        cn_override = 0
        if len(operands) >= 2:
            cn_override = self.parse_operand(operands[1], "imm1", context.get("labels", {}))
            if cn_override not in (0, 1):
                raise ValueError("Cn override musi byc 0 lub 1")

        # [7:5] opcode | [4:1] A | [0] Cn override
        word = (opcode << 5) | (a_value << 1) | cn_override
        return word

    def microcode_table(self) -> list[dict]:
        """
        Zwraca tabele mikrokodu do zaprogramowania EEPROM dekodera opcode -> 74181.
        Adres EEPROM = 3-bit opcode (0-7).
        Dane wyjsciowe = S3 S2 S1 S0 M Cn + ext_shift_enable (7 bitow), MSB->LSB.
        Dla SHR (opcode 111) ustawiane jest ext_shift_enable=1, reszta = don't care (0).
        """
        table = []
        for mnemonic, info in sorted(self.OPCODES.items(), key=lambda kv: kv[1]["opcode"]):
            opcode = info["opcode"]
            if mnemonic == "SHR":
                data = 0b0000_00_1  # S=xxxx M=x Cn=x ext_shift=1 -> tu same zera + bit shift
            else:
                s = info["S"]
                m = info["M"]
                cn = info["Cn"] if info["Cn"] is not None else 0
                data = (s << 3) | (m << 2) | (cn << 1) | 0  # ostatni bit = ext_shift_enable = 0
            table.append({
                "opcode": opcode,
                "mnemonic": mnemonic,
                "data_bin": format(data, "07b"),
                "data_hex": format(data, "02X"),
            })
        return table


# Wymagane: kazdy modul musi eksportowac zmienna ARCHITECTURE wskazujaca na klase
ARCHITECTURE = Alu4Architecture
