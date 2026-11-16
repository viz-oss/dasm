# `.import` — wklejanie plików źródłowych

`.import` wkleja cały plik `.dasm` w miejsce linii importu, **przed**
preprocesorem. Dzięki temu stałe z `.set` z zaimportowanego pliku są widoczne
w dalszej części połączonego źródła.

## Składnia

```asm
.import 'sys/c64/vic.dasm'
.import "sys/c64/vic.dasm"
.import 'sys/{OS}/vic'
.import 'lib.dasm' ; komentarz
```

- `.import` musi być pierwszą rzeczą w linii — przed nim dozwolone są tylko
  spacje i tabulatory. Nie może wystąpić po innym kodzie.
- Cudzysłowy pojedyncze i podwójne są równoważne, ale muszą się zgadzać.
- Po ścieżce może wystąpić komentarz `;`, `#` lub `//`.
- Nazwa dyrektywy jest wrażliwa na wielkość liter: `.import`, nie `.IMPORT`.
- Linia z `.import` w komentarzu jest ignorowana.
- Importowany plik jest czytany jako UTF-8. Końcowy newline jest usuwany, aby
  nie dodawać pustej linii.

## Szukanie pliku

Dla importu względnego kolejność jest następująca:

1. katalog pliku, który zawiera `.import`,
2. kolejne wpisy z `[dasm.imports].paths` (ścieżki są rozwiązywane względem
   **bieżącego katalogu uruchomienia**),
3. bieżący katalog roboczy.

Katalogi są deduplikowane po rozwiązaniu ścieżki. Jeśli nazwa nie ma
rozszerzenia, sprawdzane są dwie wersje: `nazwa` oraz `nazwa.dasm`.

Ścieżki absolutne nie są łączone z powyższymi katalogami, ale przy braku
rozszerzenia nadal sprawdzane są warianty `nazwa` i `nazwa.dasm`.

```toml
[dasm.imports]
paths = ["../lib", "lib"]
```

Klucz `[dasm.imports].repos` nie jest obecnie używany.

## Zmienne środowiskowe

W ścieżce można użyć `{NAZWA}`. Wartość pochodzi z `[dasm.env]`:

```toml
[dasm.env]
OS = "c64"
```

```asm
.import 'sys/{OS}/vic'
```

Nazwa zmiennej to `[A-Za-z_]\w*`. Brak zmiennej w `env` jest błędem:
`unknown environment variable 'MISSING' in import path ...`.

## Duplikaty i cykle

- Każdy plik jest wklejany tylko raz w całym drzewie importów.
- Kolejny import tego samego pliku zastępowany jest **pustą linią** (numeracja
  linii się nie zmienia).
- Cykl importów (`a -> b -> a`) jest błędem: `circular import: a -> b -> a`.
- Import samego siebie jest błędem (plik główny też jest na stosie).
- Kolejność wklejania jest depth-first: importowany plik jest wstawiany w
  miejscu dyrektywy, przed dalszymi liniami pliku importującego.

## Numery linii i kolumny

Wklejenie pliku zastępuje jedną linię wieloma liniami, więc numery kolejnych
linii w połączonym tekście się przesuwają. `resolve_with_map()` zwraca razem z
tekstem `SourceMap`, która pamięta segmenty:

```text
[1..11]   examples/c64.dasm      line 1
[12..89]  ../sys/c64/vic.dasm    line 1
[90..]    examples/c64.dasm      line 13
```

Dzięki temu błąd w wirtualnej linii jest raportowany względem oryginalnego
pliku i linii, a `preprocess_with_map()` dokłada `ColumnMap` korygującą
kolumny po podmianie stałych. Kontekst błędu jest odtwarzany z oryginalnej
linii pliku, a nie z tekstu po podmianie.

Błędy samego importu (brak pliku, cykl, zła zmienna env) mają od razu
ustawioną nazwę pliku (pliku importującego) oraz linię i kolumnę
`.import`. Błędy preprocesora i parsera są relokowane przez `SourceMap` w
`dasm.py`.

Pełny opis mechanizmu: [errors.md](errors.md).

## Przykład

`main.dasm`:

```asm
.import 'sys/{OS}/vic'

start:
  r0 = VIC_LIGHT_BLUE
  VIC_FRAME_COLOR = r0
```

`../sys/c64/vic.dasm`:

```asm
.set VIC_LIGHT_BLUE = 14
.set VIC_FRAME_COLOR = 0xD020
```

`build.toml`:

```toml
[dasm.env]
OS = "c64"

[dasm.imports]
paths = ["../sys"]
```

Po rozwiązaniu importu preprocesor widzi oba `.set` przed ich użyciem, a po
podmianie kod wygląda tak:

```asm
start:
  r0 = 14
  53280 = r0
```

## Ograniczenia

- Brak importu warunkowego, makr i `include` o innej semantyce.
- Brak wykrywania nieużywanych importów — wklejany jest cały plik.
- Import nie jest cyklicznie rozwiązywany względem przyszłych ścieżek z
  `paths`; katalogi są ustalane w momencie napotkania dyrektywy.
- `{NAZWA}` podstawia surową wartość z `env` (bez konwersji typów).
