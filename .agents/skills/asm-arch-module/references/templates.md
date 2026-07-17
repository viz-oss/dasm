# Szablony modułów architektury

## TEMPLATE_ALU — dla architektur ALU-only

Użyj gdy: brak skoków, brak etykiet, prosty zestaw operacji arytmetyczno-logicznych.
Przykład: alu4, alu8, własne ALU na scalakach.

```python
"""
Modul architektury: <NAZWA>
<N>-bitowe ALU, <K> operacji (<log2(K)>-bit opcode).

Format slowa instrukcji (<word_size> bit):
  [<opcode_bits>-bit opcode][<operand_bits>-bit operand A][opcjonalnie: Cn/flagi]
"""

from architectures.base import Architecture


class <Nazwa>Architecture(Architecture):

    name = "<nazwa>"
    word_size = <N>         # np. 8
    supports_labels = False

    OPCODES = {
        #  mnemonic: (opcode_val, <parametry specyficzne dla architektury>)
        "ADD": (0b000, ...),
        "SUB": (0b001, ...),
        # ...
    }

    def instruction_set(self) -> dict:
        result = {}
        for mnemonic, info in self.OPCODES.items():
            result[mnemonic] = {
                "opcode": info[0],
                "opcode_bits": <opcode_bits>,
                "operands": ["imm<operand_bits>"],
            }
        return result

    def encode(self, mnemonic: str, operands: list[str], context: dict) -> int:
        mnemonic = mnemonic.upper()
        if mnemonic not in self.OPCODES:
            raise ValueError(f"Nieznana instrukcja: {mnemonic}")

        opcode = self.OPCODES[mnemonic][0]

        if not operands:
            raise ValueError(f"{mnemonic} wymaga operandu")

        a_val = self.parse_operand(operands[0], "imm<operand_bits>", context.get("labels", {}))
        if not (0 <= a_val <= self.max_operand_value("imm<operand_bits>")):
            raise ValueError(f"Operand poza zakresem: {a_val}")

        # [opcode_bits : operand_bits]
        return (opcode << <operand_bits>) | a_val

    # Opcjonalnie: tabela mikrokodu dla EEPROM dekodera
    def microcode_table(self) -> list[dict]:
        table = []
        for mnemonic, info in sorted(self.OPCODES.items(), key=lambda kv: kv[1][0]):
            opcode = info[0]
            # ... generuj sygnaly sterujace z info
            data = 0  # WYPELNIJ
            table.append({
                "opcode": opcode,
                "mnemonic": mnemonic,
                "data_bin": format(data, "0<data_bits>b"),
                "data_hex": format(data, "02X"),
            })
        return table


ARCHITECTURE = <Nazwa>Architecture
```

---

## TEMPLATE_CPU_SIMPLE — dla prostych CPU z etykietami

Użyj gdy: prosty 8/16-bit CPU z rejestrami, skokami, pamięcią.
Przykład: własny cpu8, edukacyjny 6502-like.

```python
"""
Modul architektury: <NAZWA>
<N>-bitowy CPU, <K> rejestrów (R0-R<K-1>), <M>-bit przestrzen adresowa.

Format slowa instrukcji (<word_size> bit):
  Typ R:   [opcode][rd][rs1][rs2]
  Typ I:   [opcode][rd][imm]
  Typ J:   [opcode][addr]
"""

from architectures.base import Architecture


REG_BITS = <log2(K)>    # np. 2 dla 4 rejestrów, 3 dla 8
ADDR_BITS = <M>          # np. 8 dla 256 lokacji pamięci
IMM_BITS = <word_size> - <opcode_bits> - REG_BITS


class <Nazwa>Architecture(Architecture):

    name = "<nazwa>"
    word_size = <N>          # np. 16
    supports_labels = True   # TAK — mamy JMP/JZ z etykietami

    # Słownik: mnemonic -> (opcode, typ, [typy operandów])
    INSTRUCTIONS = {
        # Arytmetyczne (typ R: rd, rs1, rs2)
        "ADD":  (0b0000, "R", [f"reg{REG_BITS}", f"reg{REG_BITS}", f"reg{REG_BITS}"]),
        "SUB":  (0b0001, "R", [f"reg{REG_BITS}", f"reg{REG_BITS}", f"reg{REG_BITS}"]),
        # Immediate (typ I: rd, imm)
        "LOAD": (0b0100, "I", [f"reg{REG_BITS}", f"imm{IMM_BITS}"]),
        "ADDI": (0b0101, "I", [f"reg{REG_BITS}", f"imm{IMM_BITS}"]),
        # Pamięć
        "LDR":  (0b1000, "I", [f"reg{REG_BITS}", f"addr{ADDR_BITS}"]),
        "STR":  (0b1001, "I", [f"reg{REG_BITS}", f"addr{ADDR_BITS}"]),
        # Skoki (typ J: addr)
        "JMP":  (0b1100, "J", [f"addr{ADDR_BITS}"]),
        "JZ":   (0b1101, "J", [f"addr{ADDR_BITS}"]),
        "JC":   (0b1110, "J", [f"addr{ADDR_BITS}"]),
        # Specjalne
        "NOP":  (0b1111, "X", []),
        "HLT":  (0b1111, "X", []),   # może mieć ten sam opcode z sub-bit
    }

    def instruction_set(self) -> dict:
        result = {}
        for mnemonic, (opcode, itype, operands) in self.INSTRUCTIONS.items():
            result[mnemonic] = {
                "opcode": opcode,
                "opcode_bits": <opcode_bits>,
                "operands": operands,
            }
        return result

    def encode(self, mnemonic: str, operands: list[str], context: dict) -> int:
        mnemonic = mnemonic.upper()
        if mnemonic not in self.INSTRUCTIONS:
            raise ValueError(f"Nieznana instrukcja: {mnemonic}")

        opcode, itype, op_types = self.INSTRUCTIONS[mnemonic]
        labels = context.get("labels", {})

        if itype == "R":
            rd  = self.parse_operand(operands[0], op_types[0], labels)
            rs1 = self.parse_operand(operands[1], op_types[1], labels)
            rs2 = self.parse_operand(operands[2], op_types[2], labels)
            return (opcode << (3 * REG_BITS)) | (rd << (2 * REG_BITS)) | (rs1 << REG_BITS) | rs2

        if itype == "I":
            rd  = self.parse_operand(operands[0], op_types[0], labels)
            imm = self.parse_operand(operands[1], op_types[1], labels)
            return (opcode << (REG_BITS + IMM_BITS)) | (rd << IMM_BITS) | imm

        if itype == "J":
            addr = self.parse_operand(operands[0], op_types[0], labels)
            return (opcode << ADDR_BITS) | addr

        if itype == "X":  # NOP, HLT
            return opcode << (<word_size> - <opcode_bits>)

        raise ValueError(f"Nieznany typ instrukcji: {itype}")


ARCHITECTURE = <Nazwa>Architecture
```

---

## TEMPLATE_RISC — dla fixed-width 32-bit RISC

Użyj gdy: RISC-V (RV32I), własna RISC 32-bit, load-store architecture.

```python
"""
Architektura RISC 32-bit.
5 typów formatów: R, I, S, B, U, J (wzorowane na RISC-V).
32 rejestry (x0-x31), x0 zawsze = 0.
"""

from architectures.base import Architecture

OPCODE_BITS = 7
RD_BITS = RS_BITS = 5
FUNCT3_BITS = 3
FUNCT7_BITS = 7

class <Nazwa>Architecture(Architecture):

    name = "<nazwa>"
    word_size = 32
    supports_labels = True

    # Format R: funct7[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]
    # Format I: imm[31:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]
    # Format S: imm[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | imm[11:7] | opcode[6:0]
    # Format B: offset[31:12] + rd + opcode (skoki warunkowe)
    # Format J: offset 20-bit + rd + opcode (JAL)

    INSTRUCTIONS = {
        # R-type
        "ADD":  ("R", 0b0110011, 0b000, 0b0000000),
        "SUB":  ("R", 0b0110011, 0b000, 0b0100000),
        "AND":  ("R", 0b0110011, 0b111, 0b0000000),
        "OR":   ("R", 0b0110011, 0b110, 0b0000000),
        "XOR":  ("R", 0b0110011, 0b100, 0b0000000),
        # I-type
        "ADDI": ("I", 0b0010011, 0b000),
        "LW":   ("I", 0b0000011, 0b010),
        # S-type
        "SW":   ("S", 0b0100011, 0b010),
        # B-type
        "BEQ":  ("B", 0b1100011, 0b000),
        "BNE":  ("B", 0b1100011, 0b001),
        # J-type
        "JAL":  ("J", 0b1101111),
        # U-type
        "LUI":  ("U", 0b0110111),
    }

    def instruction_set(self) -> dict:
        result = {}
        for mn, info in self.INSTRUCTIONS.items():
            itype = info[0]
            if itype == "R":
                ops = ["reg5", "reg5", "reg5"]   # rd, rs1, rs2
            elif itype == "I":
                ops = ["reg5", "reg5", "imm12"]  # rd, rs1, imm
            elif itype == "S":
                ops = ["reg5", "reg5", "imm12"]  # rs1, rs2, imm (offset)
            elif itype in ("B", "J"):
                ops = ["reg5", "addr20"] if itype == "J" else ["reg5", "reg5", "rel13"]
            elif itype == "U":
                ops = ["reg5", "imm20"]
            else:
                ops = []
            result[mn] = {"opcode": info[1], "opcode_bits": 7, "operands": ops}
        return result

    def encode(self, mnemonic: str, operands: list[str], context: dict) -> int:
        mnemonic = mnemonic.upper()
        if mnemonic not in self.INSTRUCTIONS:
            raise ValueError(f"Nieznana instrukcja: {mnemonic}")
        labels = context.get("labels", {})
        info = self.INSTRUCTIONS[mnemonic]
        itype = info[0]

        def reg(tok): return self.parse_operand(tok, "reg5", labels)
        def imm(tok, bits): return self.parse_operand(tok, f"imm{bits}", labels) & ((1 << bits) - 1)

        if itype == "R":
            opcode, f3, f7 = info[1], info[2], info[3]
            rd, rs1, rs2 = reg(operands[0]), reg(operands[1]), reg(operands[2])
            return (f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | opcode

        if itype == "I":
            opcode, f3 = info[1], info[2]
            rd, rs1, i12 = reg(operands[0]), reg(operands[1]), imm(operands[2], 12)
            return (i12 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | opcode

        if itype == "S":
            opcode, f3 = info[1], info[2]
            rs1, rs2, i12 = reg(operands[0]), reg(operands[1]), imm(operands[2], 12)
            return ((i12 >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | ((i12 & 0x1F) << 7) | opcode

        raise NotImplementedError(f"Typ {itype} - dokoncz implementacje")


ARCHITECTURE = <Nazwa>Architecture
```

---

## TEMPLATE_CISC_SUBSET — dla podzbiorów CISC

Użyj gdy: x86 (podzbiór edukacyjny), 6502, Z80 (wybrane instrukcje).
Kluczowa różnica: wiele instrukcji ma różną liczbę i typy operandów.

```python
"""
Podzbiór CISC — zmienna liczba operandów na instrukcję.
Każda instrukcja definiuje własny schemat kodowania.
"""

from architectures.base import Architecture


class <Nazwa>Architecture(Architecture):

    name = "<nazwa>"
    word_size = 16   # dla uproszczonego x86-like; prawdziwe x86 jest zmienna
    supports_labels = True

    # Każda instrukcja ma własny handler encode
    # Słownik: mnemonic -> (opcode, [typy_operandow], opis)
    INSTRUCTIONS = {
        "MOV":  (0x01, ["reg4", "reg4"],  "MOV dst, src"),
        "MOVI": (0x02, ["reg4", "imm8"],  "MOV dst, immediate"),
        "ADD":  (0x03, ["reg4", "reg4"],  "ADD dst, src"),
        "ADDI": (0x04, ["reg4", "imm8"],  "ADD dst, immediate"),
        "SUB":  (0x05, ["reg4", "reg4"],  "SUB dst, src"),
        "CMP":  (0x06, ["reg4", "reg4"],  "CMP a, b (ustawia flagi)"),
        "JMP":  (0x07, ["addr8"],         "Bezwarunkowy skok"),
        "JE":   (0x08, ["addr8"],         "Skok jesli ZF=1"),
        "JNE":  (0x09, ["addr8"],         "Skok jesli ZF=0"),
        "PUSH": (0x0A, ["reg4"],          "Push na stos"),
        "POP":  (0x0B, ["reg4"],          "Pop ze stosu"),
        "CALL": (0x0C, ["addr8"],         "Wywolanie procedury"),
        "RET":  (0x0D, [],                "Powrot z procedury"),
        "NOP":  (0x0E, [],                "Brak operacji"),
        "HLT":  (0x0F, [],                "Zatrzymanie"),
    }

    # Mapa nazw rejestrów (dla CISC często mają nazwy zamiast liczb)
    REGISTERS = {
        "AX": 0, "BX": 1, "CX": 2, "DX": 3,
        "SI": 4, "DI": 5, "SP": 6, "BP": 7,
    }

    def instruction_set(self) -> dict:
        return {
            mn: {"opcode": info[0], "opcode_bits": 8, "operands": info[1]}
            for mn, info in self.INSTRUCTIONS.items()
        }

    def parse_operand(self, token: str, operand_type: str, labels: dict) -> int:
        token = token.strip().upper()
        # Nazwy rejestrów dla CISC
        if token in self.REGISTERS and operand_type.startswith("reg"):
            return self.REGISTERS[token]
        return super().parse_operand(token, operand_type, labels)

    def encode(self, mnemonic: str, operands: list[str], context: dict) -> int:
        mnemonic = mnemonic.upper()
        if mnemonic not in self.INSTRUCTIONS:
            raise ValueError(f"Nieznana instrukcja: {mnemonic}")

        opcode, op_types, _ = self.INSTRUCTIONS[mnemonic]
        labels = context.get("labels", {})

        if len(op_types) == 0:
            # NOP, RET, HLT — samo opcode w górnych bitach
            return opcode << 8

        if len(op_types) == 1:
            val = self.parse_operand(operands[0], op_types[0], labels)
            return (opcode << 8) | val

        if len(op_types) == 2:
            v0 = self.parse_operand(operands[0], op_types[0], labels)
            v1 = self.parse_operand(operands[1], op_types[1], labels)
            # [8-bit opcode][4-bit v0][4-bit v1]
            return (opcode << 8) | (v0 << 4) | v1

        raise ValueError(f"Nieoczekiwana liczba operandów: {len(op_types)}")


ARCHITECTURE = <Nazwa>Architecture
```
