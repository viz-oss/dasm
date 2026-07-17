---
name: asm-arch-module
description: |
  Tworzy nowe moduły architektury (pliki Python) dla modularnego assemblera opisanego
  w tym projekcie. Użyj tego skilla zawsze gdy użytkownik chce dodać nową architekturę
  do assemblera — np. alu8, cpu8, x86, AVR, ATtiny, ARM, Apple M, RISC-V, MIPS,
  lub własną hobbyistyczną architekturę. Triggery: "nowa architektura", "dodaj moduł",
  "napisz moduł dla", "obsłuż instrukcje X", "rozbuduj assembler o", "dodaj CPU",
  "stwórz architekturę", nazwy architektur (x86, ARM, AVR, RISC-V, ATtiny itp.).
  Skill prowadzi przez: zebranie wymagań → wybór szablonu → wypełnienie → walidację → testy.
---

# Skill: Tworzenie modułów architektury assemblera

## Cel

Każdy moduł architektury to plik `architectures/<nazwa>.py` dziedziczący po klasie
`Architecture` z `architectures/base.py`. Silnik (`assembler.py`) ładuje go dynamicznie
przez `--arch <nazwa>` — nie wymaga żadnych zmian w silniku.

Przed pisaniem kodu przeczytaj:
- `references/base_api.md` — pełne API klasy bazowej (metody, typy, co trzeba zaimplementować)
- `references/templates.md` — gotowe szablony dla typowych klas architektur
- `references/examples.md` — realne przykłady: alu4 (zbudowany), szkielety alu8/cpu8/avr

---

## Workflow

### Krok 1 — Rozpoznaj typ architektury

Zanim zaczniesz, ustal do której kategorii należy żądana architektura:

| Kategoria | Przykłady | Kluczowe cechy |
|-----------|-----------|----------------|
| **ALU-only** | alu4, alu8 | brak skoków/etykiet, brak PC, proste opcode |
| **Prosty CPU** | cpu8, własny 8-bit | etykiety, JMP/JZ, rejestry R0-Rn, PC |
| **Mikrokontroler** | ATtiny, AVR | bogaty ISA, tryby adresowania, I/O |
| **RISC** | RISC-V (RV32I), ARM Thumb | fixed-width 32/16-bit, load-store |
| **CISC** | x86 (podzbiór), 6502 | zmienna długość instrukcji, złożone tryby |
| **Eksotyczna / własna** | Apple M (ARM64 custom), DSP | specyficzne rozszerzenia |

Dla CISC/złożonych architektur — implementuj **podzbiór** (np. tylko podstawowe
instrukcje x86-64: MOV, ADD, SUB, CMP, JMP, JE, JNE, CALL, RET). Pełna x86 to
tysiące stron dokumentacji — niepraktyczne i niepotrzebne dla projektu edukacyjnego.

---

### Krok 2 — Zbierz wymagania od użytkownika

Zadaj (maksymalnie) te pytania — tylko te których odpowiedzi nie możesz wywnioskować:

1. **Jakie instrukcje muszą być obsługiwane?** (lista lub "standardowy zestaw dla X")
2. **Ile bitów ma słowo instrukcji?** (8, 16, 32 — dla znanych architektur wiadomo)
3. **Ile rejestrów i jak się nazywają?** (R0-R3, AX/BX/CX/DX, x0-x31...)
4. **Czy potrzebne są etykiety i skoki?** (TAK dla CPU, NIE dla samego ALU)
5. **Czy generować tabelę mikrokodu?** (tylko dla projektów sprzętowych z EEPROM)

Dla dobrze znanych architektur (x86, AVR, RISC-V) odpowiedz sam i potwierdź z użytkownikiem.

---

### Krok 3 — Wybierz szablon

Przeczytaj `references/templates.md` i wybierz odpowiedni szablon:

- `TEMPLATE_ALU` — dla architektur ALU-only (brak etykiet, prosty encode)
- `TEMPLATE_CPU_SIMPLE` — dla prostych CPU z etykietami i skokami
- `TEMPLATE_RISC` — dla fixed-width 32-bit RISC (load-store, pola rd/rs1/rs2)
- `TEMPLATE_CISC_SUBSET` — dla podzbiorów CISC ze zmienną długością lub trybami adresowania

---

### Krok 4 — Wypełnij moduł

Każdy moduł **musi** zawierać:

```python
from architectures.base import Architecture

class XxxArchitecture(Architecture):
    name = "xxx"           # nazwa używana w --arch
    word_size = N          # rozmiar słowa w bitach
    supports_labels = ...  # True jeśli CPU z JMP/etykietami

    def instruction_set(self) -> dict:
        # słownik: {"MNEMONIC": {"opcode": int, "opcode_bits": int, "operands": [...]}}
        ...

    def encode(self, mnemonic, operands, context) -> int:
        # logika kodowania -> zwraca int mieszczący się w word_size bitach
        ...

ARCHITECTURE = XxxArchitecture   # WYMAGANE — eksport dla silnika
```

Typy operandów (pole `"operands"` w instruction_set):
- `"imm4"`, `"imm8"`, `"imm16"` — wartość natychmiastowa (immediate) N-bitowa
- `"reg3"`, `"reg4"`, `"reg5"` — adres rejestru N-bitowy
- `"addr8"`, `"addr16"` — adres pamięci (rozwiązywany z etykiet jeśli supports_labels)
- `""` — brak operandu (instrukcje NOP, HLT itp.)

Metody pomocnicze z klasy bazowej (`base.py`) dostępne w `encode()`:
- `self.parse_operand(token, type, labels)` — parsuje dec/hex/bin/etykietę → int
- `self.max_operand_value(type)` — max wartość dla danego typu
- `self._operand_bits(type)` — liczba bitów z nazwy typu

---

### Krok 5 — Walidacja

Po wygenerowaniu kodu sprawdź (bash):

```bash
# test składni Python
python3 -c "import importlib.util; \
  spec = importlib.util.spec_from_file_location('m', 'architectures/<nazwa>.py'); \
  m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); \
  arch = m.ARCHITECTURE(); print('OK:', arch.name, arch.word_size, 'bit')"

# test assemblowania przykładowego programu
python3 assembler.py examples/<nazwa>_test.asm --arch <nazwa> --format bin
```

Jeśli architektura ma `microcode_table()`:
```bash
python3 assembler.py /dev/null --arch <nazwa> --microcode
```

Sprawdź:
- [ ] Moduł importuje się bez błędów
- [ ] `ARCHITECTURE` jest wyeksportowane
- [ ] `instruction_set()` zwraca niepusty słownik
- [ ] `encode()` dla każdej instrukcji zwraca wartość < 2^word_size
- [ ] Dla CPU: etykiety w przykładowym programie są rozwiązywane poprawnie
- [ ] Dla ALU z mikrokodem: tabela ma tyle wierszy ile opcodes

---

### Krok 6 — Utwórz plik przykładowy .asm

Zawsze twórz `examples/<nazwa>_test.asm` z co najmniej jedną instrukcją każdego
mnemonika — to dokumentacja i test w jednym. Format komentarzy:

```asm
; Architektura: <nazwa>
; Opis: <co robi ten modul>
; Format slowa: [bity opcode][bity operandow]

; --- operacje arytmetyczne ---
ADD R0, R1     ; R0 = R0 + R1
...
```

---

### Krok 7 — Dostarcz użytkownikowi

Przekaż pliki przez `present_files`:
1. `architectures/<nazwa>.py` — moduł (główny plik)
2. `examples/<nazwa>_test.asm` — przykład
3. Krótkie podsumowanie: ile instrukcji, format słowa, jak uruchomić

---

## Szczególne przypadki

### x86 (podzbiór)
- Instrukcje zmiennej długości — `word_size` ustaw na 0 lub użyj listy bajtów zamiast int
- Alternatywnie: uprość do fixed 16-bit (podzbiór edukacyjny)
- Przeczytaj `references/examples.md` sekcję "x86 subset"

### AVR / ATtiny
- 16-bit fixed słowa instrukcji
- Dwa tryby: 1-słowne (większość) i 2-słowne (LDS/STS, CALL, JMP)
- Rejestry R0-R31, ale wiele instrukcji działa tylko na R16-R31
- Przeczytaj `references/examples.md` sekcję "AVR"

### RISC-V (RV32I)
- 32-bit fixed, 32 rejestry (x0-x31), x0 zawsze = 0
- Typy instrukcji: R, I, S, B, U, J — każdy ma inny układ pól bitowych
- Przeczytaj `references/examples.md` sekcję "RISC-V"

### Własna architektura (hobby CPU)
- Użytkownik definiuje wszystko — zadaj pytania z Kroku 2
- Zasugeruj rozsądne wartości domyślne (8-bit słowo, 4 rejestry, 8 instrukcji)
- Możesz zaproponować optymalny układ bitów dla podanego zestawu instrukcji

### Apple M (ARM64)
- To ARM64 (AArch64) z Apple-specific rozszerzeniami
- Implementuj podzbiór ARM64: MOV, ADD, SUB, MUL, LDR, STR, B, BL, RET
- 32-bit fixed słowa, 32 rejestry (X0-X30 + XZR/SP)
- Przeczytaj `references/examples.md` sekcję "ARM64 subset"
---

## Czego NIE robić

- Nie modyfikuj `assembler.py` ani `architectures/base.py` — moduł ma być samowystarczalny
- Nie implementuj całej x86 — wybierz sensowny podzbiór edukacyjny
- Nie używaj zewnętrznych bibliotek (tylko stdlib Python)
- Nie zakładaj konkretnej wersji Pythona < 3.10 (używaj `list[str]` nie `List[str]`)
