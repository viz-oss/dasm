# Uruchamianie i konfiguracja

## Podstawowe użycie

```bash
python3 dasm.py program.dasm
python3 dasm.py program.dasm --arch mos6502 --format prg
python3 dasm.py program.dasm --arch wasm --format wasm -o build/program
python3 dasm.py program.dasm -d
```

`dasm.py` nie wymaga instalacji ani pakietu — wystarczy uruchomić go z katalogu
projektu (albo dodać ten katalog do `PYTHONPATH`). Wersja jest wypisywana na
początku: `dasm v2.0.2`.

## Opcje

| Opcja | Znaczenie |
|---|---|
| `source` | ścieżka do pliku wejściowego `.dasm` (wymagana) |
| `--arch NAME` | architektura: `alu48`, `arm64`, `mos6502`, `wasm`, `x86` |
| `--format NAME` | format: `bin`, `elf`, `hex`, `macho`, `prg`, `wasm`, `exe` |
| `-o`, `--output PATH` | nazwa pliku wyjściowego |
| `-d`, `--debug` | zapisuje `debug = True` w opcjach; obecnie nie ma innego efektu |
| `-l`, `--log [GRUPY]` | włącza logi: bez wartości wszystkie moduły, z wartością wybrane grupy (`lang`, `lang.preprocess`, `lang+utils`) |
| `-h`, `--help` | pomoc argparse |

> `x86`, `elf` i `exe` pozostają placeholderami bez `EXPORTS` i ich
> użycie kończy się błędem `DasmSyntaxError`. Backend `alu48` jest
> zintegrowany z `Architecture` i loaderem.

## Logowanie

Argument `-l`/`--log` włącza logi asemblera. Pusty argument loguje
wszystkie moduły; wartość filtruje grupy nazwane jak pakiety (`lang`,
`lang.preprocess`, `lang+utils`):

```bash
python3 dasm.py program.dasm --arch mos6502 --format prg --log
python3 dasm.py program.dasm --arch mos6502 --format prg --log lang.preprocess
```

Wpisy mają postać `[nazwa.loggera] komunikat` i trafiają na stdout. Domyślnie
logi są wyłączone. `--log` jest niezależny od `-d/--debug`, które tylko
ustawia opcję `debug`. Szczegóły, grupy i sposób dodawania logów w nowych
modułach opisuje [logging.md](logging.md).

## Domyślne architektura i format

Domyślna para zależy od `sys.platform`:

| System | `sys.platform` | Domyślna architektura | Domyślny format |
|---|---|---|---|
| macOS | `darwin` | `arm64` | `macho` |
| Linux | `linux`, `linux2` | `x86` | `elf` |
| Windows | `win32` | `x86` | `exe` |
| inne | — | `arm64` | `macho` |

> Na Linuksie i Windows domyślne uruchomienie nie zadziała, dopóki `x86`,
> `elf` i `exe` nie zostaną zaimplementowane. Do testów używaj wtedy jawnie
> `--arch wasm --format wasm` albo `--arch mos6502 --format prg`.

Kolejność wyboru: **argumenty CLI > `*.toml` > domyślne dla platformy**.

## Pliki `*.toml`

Po uruchomieniu DASM wczytuje **wszystkie** pliki `*.toml` z bieżącego katalogu
(posortowane po nazwie). Późniejsze pliki nadpisują wcześniejsze w `options`
i `env`, a `paths` są sklejane i deduplikowane z zachowaniem kolejności.

```toml
[dasm.options]
arch = "mos6502"
format = "prg"
debug = false

[dasm.env]
OS = "c64"
VIC_BORDER = 0xD020

[dasm.imports]
paths = ["../lib", "lib"]
```

| Sekcja | Znaczenie |
|---|---|
| `[dasm.options]` | domyślne `arch`, `format`, `debug` (z nadpisaniem przez CLI) |
| `[dasm.env]` | zmienne do `{NAZWA}` w `.import` **oraz** stałe dostępne w preprocesorze od pierwszej linii |
| `[dasm.imports].paths` | dodatkowe katalogi wyszukiwania importów (względem katalogu uruchomienia) |

Klucz `[dasm.imports].repos` może występować w plikach projektu, ale nie jest
obecnie używany. Wartości `source`/`output` w `[dasm.options]` są nadpisywane
argumentami CLI i w praktyce nie mają wpływu.

Przykład: `build.toml` w katalogu projektu ustawia `arch = "mos6502"` i
`format = "prg"`, więc `python3 dasm.py program.dasm` z tego katalogu zbuduje
plik PRG bez dodatkowych flag.

## Nazwa pliku wyjściowego

- Z `-o out` powstaje `out.<ext>` (rozszerzenie jest dopisywane, jeśli go brak).
- Z `-o out.wasm` powstaje `out.wasm` (bez podwajania rozszerzenia).
- Bez `-o` nazwa źródła jest używana z zamianą `.dasm` na `.<ext>`, np.
  `program.dasm` → `program.wasm`, `program.dasm` → `program.prg`.
- Zapis odbywa się w trybie binarnym (`wb`), więc `Format.output()` musi
  zwracać `bytes`.

## Kody wyjścia i komunikaty

| Sytuacja | Kod | Komunikat |
|---|---|---|
| sukces | `0` | kolejne etapy: `Parsing...OK`, `Architecture...<arch>`, `Assembly...OK`, `Format...<format>`, `"plik"` |
| brak pliku źródłowego | `1` | `File not found: <ścieżka>` na `stderr` |
| błąd składni/preprocesora | `1` | `<plik>:<linia>:<kolumna>: syntax error` + treść błędu na `stderr` |
| błąd argumentów | `2` | komunikat argparse |
| błąd modułu/formatowania | — | nieprzechwycony wyjątek (traceback Pythona) |

Logi (`--log`) idą na stdout i nie zmieniają kodów wyjścia; diagnostyka
błędów pozostaje na stderr. Opis systemu logów: [logging.md](logging.md).

Błędy składni są relokowane do oryginalnego pliku i linii (także po
`.import`), a kolumna do oryginalnego tekstu przed podmianą stałych. Szczegóły:
[errors.md](errors.md).

## Ładowanie modułów

Architektury i formaty są importowane dynamicznie przez
`utils.modules.load_module(dir, name)`:

1. `dir` i `name` mogą zawierać tylko litery, cyfry i `_`,
2. importowany jest moduł `dir.name` (z cache `lru_cache(32)`),
3. moduł musi eksportować `EXPORTS` będący klasą lub funkcją,
4. `load_module()` zwraca `EXPORTS()` (gotową instancję).

Brak `EXPORTS` daje `DasmSyntaxError: Module <dir>/<name>.py does not contain
EXPORTS`. Kontrakt architektur i formatów opisują
[architectures.md](architectures.md) i [formats.md](formats.md).
