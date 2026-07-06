# DASM - Modularny assembler dla własnych ALU/CPU

v0.1.0

## Struktura

```
src/
├── dasm.py                   # silnik (parser, kodowanie, wyjscie) - niezalezny od architektury
├── architectures/
│   ├── base.py               # interfejs Architecture - dziedziczy kazdy modul
│   ├── alu48.py              # modul: 4-bit ALU, 8 operacji
│   └── ...                   # tu dodajesz alu816.py, cpu816.py itd.
tests/
└── test_alu48.asm
```

## Uzycie

```bash
python3 dasm.py program.dasm --arch alu48 --format bin
python3 dasm.py program.dasm --arch alu48 --format hex -o out.hex
python3 dasm.py program.dasm --arch alu48 --format raw -o out.bin   # plik binarny do programatora EEPROM
python3 dasm.py program.dasm --arch alu48 --microcode               # tabela mikrokodu dekodera 74181
```

## Modul alu48

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

## Jak dodac nowa architekture (np. alu816, cpu816)

1. Stworz `architectures/alu816.py`.
1. Zaimportuj `from architectures.base import Architecture`.
1. Zdefiniuj klase dziedziczaca po `Architecture`:
- `name = "alu816"`
- `word_size = ...` (np. 16 dla wiekszego formatu instrukcji)
- `supports_labels = True` jesli architektura ma skoki/etykiety (np. cale CPU)
- zaimplementuj `instruction_set()` - slownik mnemonikow -> opcode/operandy
- zaimplementuj `encode(mnemonic, operands, context)` - logike kodowania slowa
1. Na koncu pliku: `ARCHITECTURE = TwojaKlasa`
1. Uzywaj: `python3 assembler.py program.asm --arch alu816`

Silnik (`assembler.py`) nie wymaga zmian - caly nowy zestaw instrukcji,
format slowa i ewentualne etykiety/skoki definiuje sie wylacznie w module
architektury. Dzieki temu rozbudowa do 8-bit ALU, a potem do calego CPU
(z pamiecia, rejestrami, JMP/JZ, mikrokodem wieloetapowym) sprowadza sie
do dopisania nowego modulu, bez modyfikacji parsera.

### Wskazowki dla wiekszych architektur

- Dla CPU z etykietami: ustaw `supports_labels = True`, a w `encode()`
  uzywaj `context["labels"]` do rozwiazywania adresow skokow (JMP/JZ).
- Dla wiekszego `word_size` (np. 16 bit) dopasuj layout bitow w `encode()`
  - reszta silnika (formatowanie wyjscia, zapis raw) skaluje sie automatycznie
    wg `word_size`.
- Mikrokod wieloetapowy (fetch/decode/execute) mozna reprezentowac jako
  dodatkowa metoda w module architektury (analogicznie do `microcode_table()`),
  generujac wieksza tabele EEPROM z licznikiem krokow jako czescia adresu.