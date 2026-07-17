# API klasy bazowej Architecture

Plik: `architectures/base.py`

## Atrybuty klasowe (do nadpisania)

```python
name: str = "base"
# Nazwa architektury używana w --arch. Musi być unikalna.

word_size: int = 8
# Rozmiar słowa instrukcji w bitach.
# Silnik używa tego do: walidacji zakresu (word >= 0, word < 2^word_size),
# formatowania wyjścia binarnego (zero-padding), zapisu raw binary.
# Dla architektur ze zmienną długością instrukcji (CISC) ustaw na największą
# możliwą długość lub zaimplementuj własny zapis.

supports_labels: bool = False
# Czy parser ma zbierać etykiety w pierwszym przebiegu.
# Ustaw True dla CPU z instrukcjami skoku (JMP, JZ, CALL itp.).
# Przy False: użycie etykiety w .asm zgłasza AssemblerError.
```

## Metody abstrakcyjne (MUSZĄ być zaimplementowane)

### `instruction_set() -> dict`

Zwraca słownik opisujący zestaw instrukcji:

```python
{
    "MNEMONIC": {
        "opcode": int,        # wartość liczbowa opcode (np. 0b000, 0x1A, 5)
        "opcode_bits": int,   # liczba bitów opcode w słowie instrukcji
        "operands": list,     # lista typów operandów, np. ["reg4", "imm8"]
                              # pusta lista [] dla instrukcji bez operandów
    },
    ...
}
```

Mnemoniki muszą być WIELKIMI LITERAMI. Silnik normalizuje wejście do upper() przed lookup.

Typy operandów — konwencja nazewnictwa:
- `"immN"` — wartość natychmiastowa (literal), N bitów (np. "imm4", "imm8", "imm16")
- `"regN"` — adres rejestru, N bitów (np. "reg3" dla 8 rejestrów, "reg5" dla 32)
- `"addrN"` — adres pamięci, N bitów; rozwiązywany z etykiet jeśli supports_labels
- `"relN"` — relatywny offset skoku, N bitów (signed, dla skoków warunkowych)
- `""` — brak operandu (NOP, HLT, RET bez argumentów)

Silnik używa `instruction_set()` do:
- walidacji czy mnemonic istnieje (przebieg 2)
- sprawdzenia minimalnej liczby operandów

### `encode(mnemonic: str, operands: list[str], context: dict) -> int`

Koduje pojedynczą instrukcję do liczby całkowitej mieszczącej się w `word_size` bitach.

Parametry:
- `mnemonic` — nazwa instrukcji, już upper() (np. "ADD", "MOV")
- `operands` — lista tokenów operandów jako stringi (np. ["R0", "5", "LOOP"])
- `context` — słownik z:
  - `context["labels"]` — dict {nazwa_etykiety: adres_int}
  - `context["address"]` — aktualny adres instrukcji (int, od 0)

Zwraca: int, 0 <= wynik < 2^word_size

Rzuca: `ValueError` z opisem błędu jeśli coś jest nie tak.
Silnik opakowuje ValueError w AssemblerError z numerem linii.

## Metody pomocnicze (dostępne w encode(), można nadpisać)

### `parse_operand(token, operand_type, labels) -> int`

Parsuje token operandu na wartość całkowitą:
- liczby dziesiętne: `"42"` → 42
- hex: `"0xFF"` lub `"0xff"` → 255
- binarnie: `"0b1010"` → 10
- rejestry: `"R3"` lub `"r3"` (gdy operand_type zaczyna się od "reg") → 3
- etykiety: `"LOOP"` → wartość z dict labels

Nadpisz tę metodę jeśli architektura ma niestandardowy format operandów
(np. `[BP+SI+4]` w x86, `%r3` w GAS, `X0` zamiast `R0` w ARM).

### `max_operand_value(operand_type) -> int`

Zwraca maksymalną wartość dla danego typu operandu:
- `"imm4"` → 15, `"imm8"` → 255, `"reg3"` → 7, `"reg5"` → 31

### `_operand_bits(operand_type) -> int` (statyczna)

Wyciąga liczbę bitów z nazwy typu: `"reg5"` → 5, `"imm16"` → 16.
Rzuca ValueError jeśli typ nie zawiera cyfr.

## Metody opcjonalne (nie w klasie bazowej, ale konwencjonalne)

### `microcode_table() -> list[dict]`

Opcjonalna. Jeśli architektura jest sprzętowa i ma dekoder EEPROM,
zaimplementuj tę metodę. Silnik ją wywołuje przy `--microcode`.

Zwraca listę słowników, każdy z kluczami:
- `"opcode"` — int
- `"mnemonic"` — str
- `"data_bin"` — str binarny (np. "1001000")
- `"data_hex"` — str hex (np. "48")

### `validate_program(words: list[int]) -> list[str]`

Opcjonalna. Walidacja całego programu po asemblacji (np. sprawdzenie
czy rozmiar nie przekracza pamięci, czy nie brakuje HLT na końcu).
Zwraca listę ostrzeżeń (stringów) lub pustą listę.
