---
name: programming-alu48
description: |
  Pisze programy w assemblerze dla architektury alu48 — 4-bitowego ALU zbudowanego
  na układzie 74181. Użyj tego skilla zawsze gdy użytkownik chce napisać program
  assemblerowy dla alu48, przetestować operacje ALU, wygenerować plik .dasm,
  zapytać "jak zapisać X w assemblerze alu48", "napisz sekwencję instrukcji",
  "wygeneruj program testowy", "jak obliczyć X na alu48", lub pyta o mnemoniki,
  operandy, format instrukcji tej architektury. Triggery: alu48, assembler 4-bit,
  74181, instrukcje ALU, program .dasm, sekwencja testowa, plik do EEPROM.
---

# Skill: Pisanie programów w assemblerze alu48

## Architektura alu48 — szybki przegląd

**alu48** to 4-bitowe ALU oparte na układzie 74181, bez rejestrów ani skoków.
Każda instrukcja = jedna operacja ALU na wartościach A i B.

- **A** — 4-bit wartość wpisana w słowie instrukcji (bit [4:1])
- **B** — 4-bit wartość ustawiana sprzętowo (przełączniki), NIE w programie
- **Cn** — carry-in, opcjonalny drugi operand (bit [0]), domyślnie 0
- Wynik pojawia się na wyjściach ALU po wykonaniu instrukcji

### Format słowa instrukcji (8 bitów)

```
  bit:  7   6   5  |  4   3   2   1  |  0
        ----opc----    ------A------    Cn
        (3-bit op)     (4-bit wartość) (carry-in)
```

### Zestaw instrukcji

| Mnemonik | Opcode | Operacja | Uwagi |
|----------|--------|----------|-------|
| `ADD`    | `000`  | A + B    | Cn=0 domyślnie; Cn=1 → A+B+1 |
| `SUB`    | `001`  | A − B    | wewnętrznie Cn=1 |
| `AND`    | `010`  | A AND B  | bitowo |
| `OR`     | `011`  | A OR B   | bitowo |
| `XOR`    | `100`  | A XOR B  | bitowo |
| `NOT`    | `101`  | NOT A    | operand B ignorowany |
| `SHL`    | `110`  | A << 1   | logiczny shift left (A+A+1) |
| `SHR`    | `111`  | A >> 1   | logika zewnętrzna (74194) |

### Składnia linii

```asm
MNEMONIC wartość_A [, Cn]   ; komentarz po średniku
```

Dozwolone formaty wartości A:
- dziesiętnie: `5`, `15`
- szesnastkowo: `0xF`, `0x0A`
- binarnie: `0b1010`

Przykłady poprawnych linii:
```asm
ADD  5          ; A=5, Cn=0
ADD  5, 1       ; A=5, Cn=1  (ADD z carry)
SUB  0xA        ; A=10
AND  0b1100     ; A=12
NOT  0          ; NOT A, operand formalnie wymagany, wartość ignorowana sprzętowo
SHR  8          ; A=8, shift right (wymaga zewnętrznego układu 74194)
```

Czego alu48 NIE obsługuje:
- etykiet i skoków (brak PC — to samo ALU, nie CPU)
- rejestrów (brak — B ustawiasz przełącznikami)
- wartości A > 15 (4 bity = 0–15)
- Cn poza {0, 1}

---

## Workflow pisania programu

### Krok 1 — Zrozum zadanie użytkownika

Ustal co program ma robić:
- Pojedyncza operacja testowa? → kilka linii
- Sekwencja testująca wszystkie instrukcje? → po jednej na mnemonic
- Obliczenie konkretnej wartości (np. `(5 AND 3) OR 7`)? → kilka kroków
- Program do zaprogramowania EEPROM? → pełna tabela, wszystkie opcje

Jeśli cel jest niejasny, zapytaj **jednym pytaniem** — np.:
> "Czy chcesz przetestować wszystkie instrukcje po kolei, czy obliczyć konkretną wartość?"

### Krok 2 — Napisz kod .dasm

Reguły dobrego kodu alu48:

1. **Jeden mnemonik na linię** — bez wieloznaczności
2. **Komentarz przy każdej linii** — co wchodzi (A=?, B=?), co wychodzi (wynik=?)
3. **Grupuj tematycznie** — arytmetyka razem, logika razem, sekcje oddzielone pustą linią
4. **Wartości czytelnie** — dla wartości bitowych używaj `0b`, dla hex `0x`, dla prostych dec
5. **Nagłówek pliku** z opisem co program testuje i jaką wartość B zakłada

Szablon nagłówka:
```asm
; Program:  <co robi>
; Arch:     alu48 (4-bit ALU, 8 istrukcji, 74181)
; Zakłada B = <wartość hex> ustawioną na przełącznikach
; Uruchom:  python3 assembler.py <plik>.dasm --arch alu48 --format bin
```

### Krok 3 — Sprawdź poprawność (walidacja w głowie)

Przed oddaniem kodu sprawdź każdą linię:
- [ ] Czy wartość A mieści się w 0–15?
- [ ] Czy Cn (jeśli podany) to 0 lub 1?
- [ ] Czy mnemonik jest z tabeli (ADD/SUB/AND/OR/XOR/NOT/SHL/SHR)?
- [ ] Czy komentarz opisuje oczekiwany wynik?

### Krok 4 — Wygeneruj plik i podaj komendę

Zawsze twórz plik .dasm przez `create_file` i podaj użytkownikowi gotowe komendy:

```bash
# Podgląd binarny (0/1)
python3 assembler.py program.dasm --arch alu48 --format bin

# Format hex (do programatora)
python3 assembler.py program.dasm --arch alu48 --format hex

# Plik binarny do EEPROM programmera
python3 assembler.py program.dasm --arch alu48 --format raw -o program.bin

# Tabela mikrokodu dekodera 74181
python3 assembler.py program.dasm --arch alu48 --microcode
```

---

## Typowe programy — przepisy

Szczegółowe przykłady gotowych programów znajdziesz w `references/programs.md`.
Przeczytaj ten plik gdy użytkownik prosi o konkretny typ programu:

- **Pełny test wszystkich instrukcji** → sekcja "Test kompletny"
- **Obliczenie wyrażenia** → sekcja "Wyrażenia arytmetyczno-logiczne"
- **Test flag carry/zero** → sekcja "Testowanie flag"
- **Program do EEPROM** → sekcja "Sekwencja do zaprogramowania sprzętu"

---

## Ograniczenia i jak je obejść

| Problem | Obejście |
|---------|----------|
| B jest stałe (przełączniki) | Zaplanuj sekwencję zakładając konkretne B; zapisz w komentarzu |
| Brak akumulatora (wynik nie jest wejściem następnej op.) | Opisz ręczne przepisanie wyniku między krokami |
| SHR wymaga zewnętrznego 74194 | Dodaj komentarz `; wymaga 74194 aktywnego` |
| NOT ignoruje B | Zawsze podaj `NOT 0` — wartość i tak ignorowana, 0 dla czytelności |
| Brak skoków/pętli | To ALU, nie CPU — powiedz użytkownikowi że potrzebuje cpu8 dla pętli |

---

## Czego NIE robić

- Nie wymyślaj instrukcji spoza tabeli (np. `MUL`, `DIV`, `MOV` — nie istnieją w alu48)
- Nie używaj etykiet — alu48 ich nie obsługuje (`supports_labels = False`)
- Nie zakładaj że wynik jednej instrukcji automatycznie wchodzi jako A do następnej — sprzętowo tak nie działa bez dodatkowego rejestru
- Nie pisz wartości A > 15 — silnik zgłosi błąd zakresu
