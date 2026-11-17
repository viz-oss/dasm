# Dokumentacja DASM

DASM to asembler wieloarchitekturowy z własnym językiem wysokopoziomowym
(rejestry wirtualne, etykiety, funkcje, dyrektywy) i wymiennymi backendami
architektur oraz formatów wyjściowych.

## Spis treści

| Dokument | Zawartość |
|---|---|
| [cli.md](cli.md) | uruchamianie `dasm.py`, opcje, `*.toml`, nazwy plików wyjściowych, kody wyjścia |
| [syntax.md](syntax.md) | składnia języka: etykiety, rejestry, przypisania, wywołania, dyrektywy |
| [preprocess_set.md](preprocess_set.md) | preprocesor: `.set`, stałe z konfiguracji, podmiany i mapowanie kolumn |
| [import.md](import.md) | `.import`, wyszukiwanie plików, zmienne środowiskowe, duplikaty i cykle |
| [logging.md](logging.md) | system logów `utils/log.py`, argument `--log`, grupy i filtry |
| [architectures.md](architectures.md) | interfejs architektury i stan implementacji backendów |
| [formats.md](formats.md) | interfejs formatu i opis formatów wyjściowych |
| [wasm.md](wasm.md) | szczegóły backendu i formatu WebAssembly |
| [errors.md](errors.md) | `DasmSyntaxError`, mapy źródeł, relokacja linii i kolumn |

## Struktura kodu

```
dasm.py              # CLI: parsowanie argumentów, potok kompilacji, zapis wyniku
arch/                # backendy architektur (wybierane przez --arch)
format/              # formaty wyjściowe (wybierane przez --format)
lang/                # leksyka, importy, preprocesor, parser, AST, symbole, błędy, mapy źródeł
utils/               # ładowanie modułów i plików *.toml, system logów
tests/               # testy jednostkowe i integracyjne
examples/            # przykłady (część to notatki projektowe, nie działający kod)
```

## Potok kompilacji

```
źródło .dasm
  → resolve_with_map()    # .import: wklejenie plików + SourceMap
  → preprocess_with_map() # .set i stałe z TOML + ColumnMap
  → parse()               # AST
  → lang.symbols.resolve() # walidacja semantyczna
  → Architecture.assembly()
  → Format.output()
  → plik wyjściowy
```

`dasm.py` wywołuje `resolve()` przed assembly, dzięki czemu rejestry argumentów
wywołań są uzupełniane, a błędy symboli są zgłaszane przed generowaniem kodu.

## Stan implementacji

| Architektura | Stan |
|---|---|
| `arm64` | częściowa: `mov` stałej do rejestru (`MOVZ`); reszta `NotImplementedError` |
| `mos6502` | częściowa: immediates, zapis absolutny, `call`/`ret`/`exit`/`jmp`; większość trybów adresowania to stuby |
| `wasm` | mov/load/store, `return`, `exit`; brak `call`/`jmp` i adresów etykiet |
| `x86` | placeholder (brak kodu i `EXPORTS`) |
| `alu48` | legacy, poza interfejsem `Architecture`; nie działa przez CLI |

| Format | Stan |
|---|---|
| `bin` | gotowy |
| `prg` | gotowy (C64) |
| `hex` | gotowy (tekstowy hex) |
| `macho` | gotowy dla pojedynczej sekcji `__text` |
| `wasm` | gotowy dla pojedynczej funkcji |
| `elf` | placeholder (brak `EXPORTS`) |
| `exe` | placeholder (brak `EXPORTS`) |

> Domyślne pary zależą od systemu: macOS `arm64` + `macho`, Linux `x86` +
> `elf`, Windows `x86` + `exe`. Na Linuksie i Windows domyślne uruchomienie
> zakończy się błędem, dopóki `x86`, `elf` i `exe` pozostają placeholderami.
