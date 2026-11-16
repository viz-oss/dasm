# Formaty wyjściowe

Format zamienia listę słów (`list[int]`) na bajty pliku. Wybór odbywa się przez
`--format NAME` lub `[dasm.options].format`.

## Interfejs `Format`

Plik `format/base.py`:

```python
class Format(ABC):
    ext = ''            # rozszerzenie pliku wyjściowego
    origin = 0          # adres pierwszego bajtu kodu (dla etykiet/relokacji)
    entry_jump = False  # czy przed kodem wstawić skok do .start

    def output(self, words: list[int], entry: int | None = None) -> bytes
```

- `origin` jest przekazywany do `Architecture.assembly()` jako adres bazowy.
- `entry_jump = True` powoduje, że CLI każe architekturze wstawić skok do
  etykiety z `.start` (o ile `.start` występuje).
- `entry` to wyliczony adres punktu wejścia; większość formatów go ignoruje.
- `output()` **musi zwracać `bytes`**, bo CLI zapisuje plik w trybie `wb`.

## `bin` — surowy binarny

```python
return bytes(words)
```

- `ext = 'bin'`, `origin = 0`, `entry_jump = False`.
- Bez nagłówka, bez relokacji adresu ładowania; `entry` ignorowane.

## `prg` — C64 PRG

Plik `format/prg.py` buduje:

```
offset 0   : 2 B  nagłówek z adresem ładowania 0x0801 (little endian)
offset 2   : 12 B stub BASIC
offset 14  : kod programu (od adresu 0x080D)
```

Stub BASIC to linia `10 SYS 2061` (`0x9E` + cyfry `2061`) zakończona `0x00`
oraz `0x00 0x00`. `origin = 0x080D` (`2061`), `entry_jump = True`, więc przy
`.start` na początku kodu pojawia się `JMP <entry>`.

- `ext = 'prg'`, dziedziczy po `FormatBin` (`output` zlepia części).
- `entry` nie jest używany — adres w stubie BASIC jest stały (`SYS 2061`).

## `hex` — tekstowy hex

```
1234
0001
```

- `ext = 'hex'`, `origin = 0`, `entry_jump = False`.
- Każde słowo jest formatowane jako co najmniej 4 cyfry szesnastkowe
  (wielkie litery), słowa oddzielone `\n`, bez końcowego newline.
- Wynik jest kodowany ASCII i zwracany jako `bytes`.
- `entry` ignorowane. Wartości większe niż `0xFFFF` wypiszą więcej niż 4 cyfry.

## `macho` — Mach-O dla Apple Silicon

Pojedynczy obiekt `MH_OBJECT` z sekcją `__text` i pustą tablicą symboli:

```
offset 0    : mach_header_64             (32 B)
offset 32   : LC_SEGMENT_64 + section_64 (152 B)
offset 184  : LC_SYMTAB                  (24 B)
offset 208  : __text: słowa jako uint32 LE
             : tablica symboli            (0 wpisów)
             : string table               (bajt NUL)
```

- `ext = 'o'`, `origin = 0`, `entry_jump = False`.
- Nagłówek: magic `0xFEEDFACF`, CPU `0x0100000C` (ARM64), typ `MH_OBJECT`,
  `ncmds = 2`, `sizeofcmds = 176`.
- Sekcja `__text` ma `align = 2` (4 bajty), flagi
  `S_ATTR_PURE_INSTRUCTIONS | S_ATTR_SOME_INSTRUCTIONS`.
- Każde słowo trafia do pliku jako 32-bit `uint32` little endian; słowa muszą
  mieścić się w 32 bitach.
- Brak relokacji i symboli; `entry` ignorowane.

## `wasm` — moduł WebAssembly

Format opakowuje strumień opcodów z `arch/wasm.py` w kompletny moduł:
magic/version, sekcje type, function, opcjonalnie memory, export i code.

- `ext = 'wasm'`, `origin = 0`, `entry_jump = False`.
- `memory_pages = 1` (minimum pamięci liniowej), `export_name = 'main'`.
- Sekcja `memory` i eksport `memory` pojawiają się tylko przy użyciu
  `i32.load`/`i32.store`.
- Wymaga, by strumień kończył się opcodem `end` (`0x0B`).
- `entry` musi być `None` albo `0`; inny adres daje `ValueError`.

Szczegóły: [wasm.md](wasm.md).

## `elf` — placeholder

Plik `format/elf.py` zawiera tylko docstring. Brak `EXPORTS`, więc
`--format elf` kończy się
`DasmSyntaxError: Module format/elf.py does not contain EXPORTS`.

## `exe` — placeholder (Windows)

Plik `format/exe.py` zawiera tylko docstring `"""Windows .exe"""`. Brak
`EXPORTS`, więc `--format exe` kończy się analogicznym błędem. Jest to
domyślny format na Windows, więc domyślne uruchomienie na Windows nie zadziała
do czasu implementacji.

## Interakcja `.start` z formatem

```asm
.start main
main:
    r0 = 1
```

CLI wyciąga `main` z AST i przekazuje `start='main'` do architektury, a
`entry_jump = format.entry_jump`. Skutki:

| Format | `entry_jump` | Efekt `.start` |
|---|---|---|
| `prg` | `True` | na początku kodu pojawia się `JMP main` |
| `bin`, `hex`, `macho`, `wasm`, `elf`, `exe` | `False` | brak skoku; `entry` trafia do `output()` (zwykle ignorowane) |

W `wasm` niezerowy `entry` jest błędem, więc `.start` z etykietą poza
offsetem 0 nie zadziała. Dla `mos6502` + `prg` skok wejściowy ma 3 bajty i
przesuwa adresy etykiet.

## Dodawanie formatu

1. Utwórz `format/nazwa.py` z klasą dziedziczącą po `format.base.Format`.
2. Ustaw `ext`, `origin` i `entry_jump`.
3. Zaimplementuj `output(words, entry=None) -> bytes`.
4. Dodaj `EXPORTS = TwojaKlasa`.
5. Dopisz `nazwa` do `choices` w `--format` w `dasm.py` i testy.

Więcej: [development.md](development.md).
