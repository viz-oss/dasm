# Gotowe programy i przepisy dla alu48

## Test kompletny (wszystkie 8 instrukcji)

Zakłada B = 0x3 (0011) ustawione na przełącznikach.
Testuje każdy mnemonik po jednym razie, z czytelnym komentarzem co powinno wyjść.

```asm
; Program:  Kompletny test wszystkich instrukcji alu48
; Arch:     alu48 (4-bit ALU, 8 instrukcji, 74181)
; Zakłada:  B = 0x3 (0011) na przełącznikach
; Uruchom:  python3 assembler.py test_all.dasm --arch alu48 --format bin

; --- arytmetyka ---
ADD  5          ; A=0101, B=0011 → wynik=1000 (8), Carry=0
ADD  5, 1       ; A=0101, B=0011, Cn=1 → wynik=1001 (9)
SUB  7          ; A=0111, B=0011 → wynik=0100 (4)

; --- logika bitowa ---
AND  0b1111     ; A=1111, B=0011 → wynik=0011 (3)
OR   0b1100     ; A=1100, B=0011 → wynik=1111 (15)
XOR  0b1010     ; A=1010, B=0011 → wynik=1001 (9)
NOT  0          ; NOT A=0000 → wynik=1111 (15), B ignorowane

; --- przesunięcia ---
SHL  4          ; A=0100 → wynik=1000 (8), Carry z bitu 3
SHR  8          ; A=1000 → wynik=0100 (4), wymaga 74194
```

---

## Wyrażenia arytmetyczno-logiczne

Alu48 nie ma akumulatora — wynik każdej operacji trzeba ręcznie odczytać
z wyjść i ewentualnie ustawić jako nowe A (lub B na przełącznikach).
Komentarze opisują co odczytać po każdym kroku.

### Przykład: oblicz (5 AND 3) OR 7

```asm
; Krok 1: oblicz 5 AND 3
; Ustaw B=3 (0011) na przełącznikach
AND  5       ; A=0101, B=0011 → wynik=0001 (1)  ← odczytaj wynik=1

; Krok 2: oblicz wynik OR 7
; Ustaw A=1 (wynik z kroku 1) przez nową instrukcję, B=7 (0111)
OR   1       ; A=0001, B=0111 → wynik=0111 (7)  ← wynik końcowy = 7
```

### Przykład: oblicz NOT (A AND B) czyli NAND

```asm
; Ustaw B=0xA (1010) na przełącznikach
AND  0b1100  ; A=1100, B=1010 → wynik=1000 (8)
; Odczytaj wynik=8, ustaw jako nowe A
NOT  8       ; NOT 1000 → wynik=0111 (7)  ← NAND(1100, 1010) = 0111
```

### Przykład: sprawdź czy A == B (przez XOR)

```asm
; Ustaw B=5 (0101) na przełącznikach
; Jeśli A==B, XOR da 0, flaga Zero=1
XOR  5       ; A=0101, B=0101 → wynik=0000, Zero=1  ← równe!
XOR  3       ; A=0011, B=0101 → wynik=0110, Zero=0  ← różne
```

---

## Testowanie flag carry i zero

74181 wystawia flagi: Cn+4 (carry out), Zero (=0 gdy wynik=0000).

```asm
; Program:  Test flag Carry i Zero
; Arch:     alu48
; Zakłada:  B = 0xF (1111) na przełącznikach

; --- test Carry (przepełnienie dodawania) ---
ADD  15      ; A=1111 + B=1111 = 11110, Carry=1  ← obserwuj pin Cn+4
ADD  1       ; A=0001 + B=1111 = 10000, Carry=1
ADD  0       ; A=0000 + B=1111 = 01111, Carry=0

; --- test Zero ---
; Ustaw B=5 (0101) na przełącznikach
XOR  5       ; A=0101 XOR B=0101 = 0000, Zero=1   ← flaga Zero aktywna
AND  0       ; A=0000 AND B=0101 = 0000, Zero=1
OR   1       ; A=0001 OR  B=0101 = 0101, Zero=0

; --- test SUB dający zero ---
; Ustaw B=7 (0111) na przełącznikach
SUB  7       ; A=0111 - B=0111 = 0000, Zero=1, Carry=1 (borrow=0)
```

---

## Sekwencja do zaprogramowania sprzętu (EEPROM / sekwencer)

Gdy chcesz zaprogramować sekwencer lub pamięć programu fizycznego układu.
Format `raw` generuje plik binarny gotowy do programatora EEPROM (np. TL866).

```asm
; Program:  Sekwencja inicjalizacyjna hardware
; Arch:     alu48
; Przeznaczenie: plik do programatora EEPROM (TL866, CH341A itp.)
; Zakłada:  B ustawiane zewnętrznie przez każdym krokiem

; Reset/inicjalizacja - zeruj przez XOR z samym sobą
XOR  0       ; jeśli A=B=0, wynik=0 (czyszczenie)

; Weryfikacja sumatora
ADD  0x5     ; A=5, oczekiwany wynik zależy od B
ADD  0xA     ; A=10

; Weryfikacja logiki
AND  0xF     ; AND z B (przekazuje B na wyjście)
OR   0x0     ; OR z 0 (przekazuje B na wyjście)
XOR  0xF     ; XOR z 1111 = NOT B

; Weryfikacja NOT
NOT  0       ; NOT A=0 → 1111 zawsze
NOT  0xF     ; NOT A=1111 → 0000 zawsze

; Shift
SHL  1       ; 0001 → 0010
SHL  2       ; 0010 → 0100
SHL  4       ; 0100 → 1000
```

Generowanie pliku binarnego:
```bash
python3 assembler.py sekwencja.dasm --arch alu48 --format raw -o sekwencja.bin
```

---

## Tabela mikrokodu dekodera 74181

Nie jest to program .dasm — to tabela do programowania EEPROM dekodera opcodes.
Generujesz ją komendą bez pliku wejściowego:

```bash
python3 assembler.py examples/test_alu48.dasm --arch alu48 --microcode
```

Wynik (adres EEPROM = 3-bit opcode, dane = S3 S2 S1 S0 M Cn ext_shift):

```
Opcode  Mnemonik  Dane (bin)  Dane (hex)
000     ADD       1001000     48
001     SUB       0110010     32
010     AND       1011100     5C
011     OR        1110100     74
100     XOR       0110100     34
101     NOT       0000100     04
110     SHL       0000010     02
111     SHR       0000001     01
```

Wgraj tę tabelę do EEPROM dekodera (np. 28C16):
- adresy 0x00–0x07 = powyższe wartości
- reszta pamięci = 0x00 (nieużywane)

---

## Częste błędy i ich naprawa

| Błąd w .dasm | Komunikat silnika | Naprawa |
|--------------|-------------------|---------|
| `ADD 16` | `Operand A poza zakresem 0-15: 16` | Max to 15 → użyj `ADD 0xF` |
| `MOV 5` | `Nieznana instrukcja: MOV` | MOV nie istnieje w alu48 |
| `ADD R0, R1` | `Operand A poza zakresem` | Brak rejestrów — użyj wartości liczbowej |
| `LOOP: ADD 5` | `Architektura 'alu48' nie wspiera etykiet` | Usuń etykietę — alu48 to nie CPU |
| `ADD 5, 2` | `Cn override musi byc 0 lub 1` | Cn to tylko 0 lub 1, nie 2 |
| `SHR 8` (brak 74194) | asembluje OK, ale sprzęt nie działa | Dodaj układ 74194 do płytki |
