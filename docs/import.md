# `.import` — wklejanie plików źródłowych

`.import` wkleja cały plik `.dasm` w miejsce linii importu, przed
preprocesorem. Dzięki temu stałe z `.set` z zaimportowanego pliku są widoczne
w dalszej części połączonego źródła.

## Składnia

```asm
.import 'sys/c64/vic.dasm'
.import "sys/c64/vic.dasm"
.import 'sys/{OS}/vic'
```

- Import musi być pierwszą znaczącą rzeczą w linii.
- Cudzysłowy pojedyncze i podwójne są równoważne.
- Po ścieżce może wystąpić komentarz (`;`, `#`, `//`).
- `.import` wewnątrz komentarza jest ignorowany.

## Szukanie pliku

Dla importu względnego kolejność jest następująca:

1. katalog pliku, który zawiera `.import`,
2. kolejne wpisy z `[dasm.imports].paths` (względem katalogu uruchomienia),
3. bieżący katalog roboczy.

Jeśli nazwa nie ma rozszerzenia, sprawdzane są dwie wersje: `nazwa` oraz
`nazwa.dasm`. Ścieżki absolutne są używane bez zmian.

```toml
[dasm.imports]
paths = [".."]
```

## Zmienne środowiskowe

W ścieżce można użyć `{NAZWA}`. Wartość pochodzi z `[dasm.env]`:

```toml
[dasm.env]
OS = "c64"
```

```asm
.import 'sys/{OS}/vic'
```

Brak zmiennej w `env` jest błędem.

## Duplikaty i cykle

- Każdy plik jest wklejany tylko raz w całym drzewie importów.
- Kolejny import tego samego pliku zastępowany jest pustą linią.
- Cykl importów (`a -> b -> a`) jest błędem.
- Import samego siebie jest błędem.

## Numery linii

Wklejenie pliku zastępuje jedną linię wieloma liniami, więc numery kolejnych
linii w połączonym tekście się przesuwają. Błędy parsera odnoszą się do
połączonego tekstu, natomiast błędy samego importu zawierają nazwę pliku i
numer linii, w której wystąpił `.import`.

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

Po rozwiązaniu importu preprocesor widzi oba `.set` przed ich użyciem.
