# Przykłady modułów architektur

## Zrealizowany: alu4

Plik: `architectures/alu4.py` (w projekcie)

- 8-bit słowo, 3-bit opcode, 8 operacji
- Brak etykiet, operand A 4-bit + Cn override
- Metoda `microcode_table()` generuje tabelę dla EEPROM dekodera 74181
- Format: `[opc2 opc1 opc0 | A3 A2 A1 A0 | Cn]`

Uruchomienie:
```bash
python3 assembler.py examples/test_alu4.asm --arch alu4 --format bin
python3 assembler.py anything --arch alu4 --microcode
```

---

## Szkielet: alu8

8-bitowe ALU z 16 operacjami (4-bit opcode), 8-bit operand A, 16-bit słowo.

```python
from architectures.base import Architecture

class Alu8Architecture(Architecture):
    name = "alu8"
    word_size = 16
    supports_labels = False

    OPCODES = {
        "ADD":  (0x0, 0b1001, 0, 0),   # S=1001 M=0 Cn=0
        "ADDC": (0x1, 0b1001, 0, 1),   # ADD z carry
        "SUB":  (0x2, 0b0110, 0, 1),
        "SUBB": (0x3, 0b0110, 0, 0),   # SUB z borrow
        "AND":  (0x4, 0b1011, 1, 0),
        "OR":   (0x5, 0b1110, 1, 0),
        "XOR":  (0x6, 0b0110, 1, 0),
        "XNOR": (0x7, 0b1001, 1, 0),
        "NOT":  (0x8, 0b0000, 1, 0),
        "SHL":  (0x9, 0b0000, 0, 1),
        "SHR":  (0xA, None,   None, None),  # zewnętrzna logika
        "ASHR": (0xB, None,   None, None),  # arytmetyczny shift right
        "CLR":  (0xC, 0b0011, 0, 0),   # A = 0
        "SET":  (0xD, 0b1111, 1, 0),   # A = 0xFF
        "INC":  (0xE, 0b0000, 0, 1),   # A + 1
        "DEC":  (0xF, 0b1111, 0, 0),   # A - 1
    }

    def instruction_set(self):
        return {
            mn: {"opcode": v[0], "opcode_bits": 4, "operands": ["imm8"]}
            for mn, v in self.OPCODES.items()
        }

    def encode(self, mnemonic, operands, context):
        mnemonic = mnemonic.upper()
        opcode = self.OPCODES[mnemonic][0]
        a = self.parse_operand(operands[0], "imm8", context.get("labels", {}))
        if not (0 <= a <= 255):
            raise ValueError(f"Operand poza zakresem 0-255: {a}")
        # [4-bit opcode][8-bit A][4-bit rezerwa/flagi]
        return (opcode << 12) | (a << 4)

ARCHITECTURE = Alu8Architecture
```

Przykładowy program `examples/test_alu8.asm`:
```asm
; Test alu8 - 16-bit slowo, 16 operacji
ADD  0xFF     ; A=255, ADD
SUB  0x0F     ; A=15, SUB
AND  0b10101010
SHL  64
CLR  0        ; zeruj (operand ignorowany)
INC  0
```

---

## Szkielet: cpu8 (prosty 8-bit CPU z etykietami)

16-bit słowo instrukcji, 4 rejestry (R0-R3), 8-bit przestrzeń adresowa.

```python
from architectures.base import Architecture

REG_BITS = 2   # 4 rejestry
ADDR_BITS = 8  # 256 lokacji
OPCODE_BITS = 4
IMM_BITS = 8

class Cpu8Architecture(Architecture):
    name = "cpu8"
    word_size = 16
    supports_labels = True

    INSTRUCTIONS = {
        # Typ R: [opcode 4b][rd 2b][rs 2b][00 8b]
        "ADD":  ("R", 0x0), "SUB": ("R", 0x1),
        "AND":  ("R", 0x2), "OR":  ("R", 0x3),
        "XOR":  ("R", 0x4), "MOV": ("R", 0x5),
        # Typ I: [opcode 4b][rd 2b][imm 10b]
        "LOADI": ("I", 0x6),
        # Typ M: [opcode 4b][rd 2b][addr 10b]  (load/store z pamięci)
        "LDR":  ("M", 0x7), "STR": ("M", 0x8),
        # Typ J: [opcode 4b][addr 12b]
        "JMP":  ("J", 0x9), "JZ":  ("J", 0xA),
        "JC":   ("J", 0xB), "JN":  ("J", 0xC),
        "CALL": ("J", 0xD),
        # Typ X: brak operandów
        "NOP":  ("X", 0xE), "HLT": ("X", 0xF),
    }

    def instruction_set(self):
        ops_map = {
            "R": [f"reg{REG_BITS}", f"reg{REG_BITS}"],
            "I": [f"reg{REG_BITS}", f"imm{IMM_BITS}"],
            "M": [f"reg{REG_BITS}", f"addr{ADDR_BITS}"],
            "J": [f"addr{ADDR_BITS}"],
            "X": [],
        }
        return {
            mn: {"opcode": v[1], "opcode_bits": OPCODE_BITS,
                 "operands": ops_map[v[0]]}
            for mn, v in self.INSTRUCTIONS.items()
        }

    def encode(self, mnemonic, operands, context):
        itype, opcode = self.INSTRUCTIONS[mnemonic.upper()]
        labels = context.get("labels", {})
        r = lambda t, tp: self.parse_operand(t, tp, labels)

        if itype == "R":
            rd  = r(operands[0], f"reg{REG_BITS}")
            rs  = r(operands[1], f"reg{REG_BITS}")
            return (opcode << 12) | (rd << 10) | (rs << 8)
        if itype in ("I", "M"):
            rd  = r(operands[0], f"reg{REG_BITS}")
            val = r(operands[1], f"imm{IMM_BITS}")
            return (opcode << 12) | (rd << 10) | (val & 0x3FF)
        if itype == "J":
            addr = r(operands[0], f"addr{ADDR_BITS}")
            return (opcode << 12) | (addr & 0xFFF)
        if itype == "X":
            return opcode << 12
        raise ValueError(f"Nieznany typ: {itype}")

ARCHITECTURE = Cpu8Architecture
```

Przykładowy program z etykietami:
```asm
; Prosty licznik: R0 = 0, liczy do 10
        LOADI R0, 0     ; R0 = 0
        LOADI R1, 10    ; R1 = 10 (max)
LOOP:   ADD   R0, R2   ; R0 = R0 + R2 (zakładamy R2=1)
        CMP   R0, R1   ; porównaj (w uproszczeniu - tu brakuje CMP, dodaj)
        JZ    DONE     ; jeśli zero -> koniec
        JMP   LOOP
DONE:   HLT
```

---

## Notatki: AVR / ATtiny

Kluczowe fakty dla implementacji:
- 16-bit fixed słowa (większość instrukcji), 2-słowne: LDS, STS, CALL, JMP
- 32 rejestry R0-R31; instrukcje arytmetyczne tylko na R16-R31
- Przestrzeń programu: 16-bit (do 64K słów = 128KB), ATtiny2313: 1K słów
- Ważne instrukcje: MOV, LDI, ADD, ADC, SUB, SBC, AND, OR, EOR, COM, NEG,
  INC, DEC, LSL, LSR, ASR, RJMP, RCALL, RET, RETI, BRNE, BREQ, NOP, SLEEP

Format RJMP (relative jump, 1 słowo):
```
[1100 | k11..k0]  gdzie k = offset -2048..+2047 (w słowach)
```

Format ADD:
```
[000011 | rd4 | rr4]  rd i rr to 4 bity (R0-R31 = 5 bitów, ale instrukcja używa ciekawe kodowanie)
```

Zalecenie: zacznij od podzbioru: LDI, MOV, ADD, SUB, AND, OR, EOR, RJMP, BRNE, NOP, RET

---

## Notatki: ARM64 / Apple M (AArch64)

Apple M to ARM64 z extensions (AMX, Neural Engine) - te są zamknięte.
Rdzeń ARM64 jest dobrze udokumentowany.

Kluczowe:
- 32-bit fixed słowa
- 32 rejestry: X0-X30 (64-bit), W0-W30 (32-bit dolne), XZR/WZR (zero), SP
- Tryby adresowania: base, base+offset, pre-index, post-index

Format instrukcji ADD (extended register):
```
[sf(1) | 00001011 | shift(2) | 0 | Rm(5) | imm6(6) | Rn(5) | Rd(5)]
```

Dla modułu assemblera zalecany podzbiór:
```
MOV Xd, Xn          ; move
MOV Xd, #imm16      ; move immediate
ADD Xd, Xn, Xm      ; add
SUB Xd, Xn, Xm      ; subtract
MUL Xd, Xn, Xm      ; multiply
LDR Xd, [Xn]        ; load
STR Xd, [Xn]        ; store
B label              ; branch
BL label             ; branch and link (call)
RET                  ; return
CMP Xn, Xm          ; compare (sets flags)
B.EQ / B.NE label   ; conditional branch
```

---

## Notatki: x86 (podzbiór edukacyjny)

Prawdziwe x86 ma zmienną długość instrukcji (1-15 bajtów) - niepraktyczne do pełnej implementacji.

Dla modułu edukacyjnego: fixed 32-bit lub fixed 16-bit uproszczone.

Jeśli user chce "prawdziwy" x86 output (np. do nauki debuggowania):
- Implementuj jako listę bajtów zamiast int
- Lub użyj zewnętrznej biblioteki (keystone, nasm subprocess)
- Zaznacz użytkownikowi że to wykracza poza silnik

Minimalny edukacyjny podzbiór x86 (fixed 16-bit uproszczone):
```
MOV AX, BX / MOV AX, 0x1234
ADD AX, BX / ADD AX, 0x10
SUB, CMP, AND, OR, XOR
JMP, JE, JNE, JL, JG
PUSH, POP
CALL, RET
NOP, HLT
INT 0x21   ; DOS interrupt (dla programów DOS-like)
```
