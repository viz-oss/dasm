# Preprocesor: `.set` i stałe konfiguracyjne

Preprocesor działa **przed parserem**, na tekście po rozwiązaniu `.import`
(i przed mapowaniem błędów). Zamienia wybrane nazwy na wartości oraz usuwa
linie `.set`, zachowując numerację linii.

## Składnia

```asm
.set NAZWA = 123
.set KOLOR = 0xD020
.set UJEMNA = -5
.set BIN = 0b1010
.set SEP = 1_000
.set TEKST = "Hello\n"
```

- Nazwa stałej to identyfikator: litery Unicode, cyfry, `_` i emoji; nie może
  zaczynać się od cyfry ani nazywać się `rN`.
- Wartość to liczba albo string w podwójnych cudzysłowach.
- Liczby są parsowane jak w Pythonie z base 0: dziesiętne, `0x...`, `0b...`,
  `0o...`, z `_` i znakiem `-`.
- Stringi używają escape'ów Pythona (`\n`, `\"`, `\\`). Wynik jest z powrotem
  wstawiany w formie JSON, czyli w podwójnych cudzysłowach.
- `.set` musi być pierwszą znaczącą rzeczą w linii (poza spacjami/tabami).

## Jednoprzebiegowość

Stała musi być zdefiniowana **przed użyciem**. Preprocesor idzie od góry do
dołu i nie robi wstępnego zbierania definicji:

```asm
r0 = X          ; X nie jest jeszcze znane → pozostaje jako Ptr('X')
.set X = 1
```

Użycie przed definicją nie jest błędem — po prostu nazwa zostaje nazwą
(etykietą/adresem). Jeśli chcesz używać stałych w całym pliku, zdefiniuj je na
początku albo w zaimportowanym pliku, który jest wklejany przed kodem.

## Stałe z konfiguracji

Klucze z `[dasm.env]` w `*.toml` są dostępne jako stałe **od pierwszej linii**:

```toml
[dasm.env]
OS = "c64"
VIC_BORDER = 0xD020
```

```asm
r0 = VIC_BORDER
```

Zasady:

- konfiguracja **wygrywa** z `.set` o tej samej nazwie (wartość z TOML nie
  zostanie nadpisana),
- linia `.set` dla takiej nazwy jest nadal walidowana (nie może być błędna),
- dozwolone są tylko `int` i `str`; `bool` jest odrzucany mimo dziedziczenia
  po `int`,
- nazwy kluczy są walidowane tak samo jak nazwy stałych.

Te same wartości `[dasm.env]` służą do rozwijania `{NAZWA}` w `.import` — patrz
[import.md](import.md).

## Co jest podmieniane

Podmieniane są wyłącznie tokeny typu **name** (nazwy w kodzie). Nie są
podmieniane:

- komentarze (`;`, `#`, `//`),
- stringi,
- etykiety (`X:` to osobny token),
- nazwy dyrektyw (`.set`, `.raw`, `.start`, ...).

```asm
.set X = 1
; X              ← komentarz, bez zmian
// X             ← komentarz, bez zmian
r0 = "X"         ← string, bez zmian
X:               ← etykieta, bez zmian
.raw("ascii") "X" ← string, bez zmian
r0 = X           ← podmiana na 1
```

## Numeracja linii i kolumn

Linia `.set` jest zastępowana **pustą linią**, więc numery linii w błędach
parsera pozostają zgodne z plikiem źródłowym.

`preprocess_with_map()` zwraca `PreprocessedSource(text, column_maps)`.
Dla każdej linii powstaje `ColumnMap`, która mapuje kolumny po podmianie na
oryginalne kolumny. Cała podstawiona wartość (np. `1000` za `X`) wskazuje na
pierwszą kolumnę nazwy stałej. Dzięki temu błąd w `r0 = 1000 +` jest
raportowany przy `X`, a kontekst pokazuje oryginalne `r0 = X +`.

Szczegóły: [errors.md](errors.md).

## Błędy

| Sytuacja | Komunikat |
|---|---|
| nazwa `rN` | `'r1' is reserved for registers` |
| nieprawidłowa nazwa (np. z TOML) | `invalid constant name 'bad-name'` |
| wartość nie jest liczbą/stringiem | `constant value must be a number or a string: 'abc'` |
| zła liczba (np. `09`) | `invalid number '09'` |
| zły string (np. `"\x"`) | `invalid string literal` |
| brak nazwy/wartości | `expected: .set NAME = <number or string>` |
| duplikat `.set` | `constant 'X' already defined` |
| zły typ w TOML | `config constant 'X': expected int or string, got bool` |

## Decyzje projektowe

- Stała musi być zdefiniowana przed użyciem; jeden przebieg z góry na dół.
  Gdyby stałe miały działać w całym pliku niezależnie od kolejności, potrzebny
  byłby przebieg zbierający `.set`, a potem drugi z podmianą.
- Stałe nie mogą nazywać się `rN`, spójnie z regułą rejestrów.
- `.set` zostawia pustą linię, żeby numery linii w błędach parsera się zgadzały.
- Wartości liczbowe są normalizowane do postaci dziesiętnej: `0xFF` wraca do
  tekstu jako `255`. Stringi wracają w formie JSON (podwójne cudzysłowy).
- Kolumny po podmianie są korygowane przez `ColumnMap`.

## Otwarte kwestie

- **Stała użyta jako wywołanie.** `art()` to token `name`, więc stała `art`
  zostałaby zamieniona i dałaby `1()` oraz mylący błąd składni. Warto dodać
  wyjątek: jeśli następnym znaczącym tokenem jest `(`, zgłosić
  `constant used as a call`.
- **Stała po lewej stronie.** `art = r0` po podmianie to `1 = r0`, czyli cichy
  zapis pod adres 1. Może być zamierzone, ale łatwo o pomyłkę.
- **Duplikacja reguł leksykalnych.** `_TOKEN_RE` w preprocesorze powtarza
  fragmenty gramatyki (komentarze, stringi, `NAME`, `LABEL`). Zmiana składni
  w jednym miejscu bez drugiego może rozjechać preprocesor i parser. Warto
  wspólne stałe regexów albo test porównujący oba na tych samych przykładach.
- **Kolizja nazwy stałej i etykiety.** Przy `.set art = 1` i etykiecie `art:`
  etykieta zostaje (osobny token), ale `r0 = art` da `r0 = 1` zamiast adresu
  etykiety. Wykrycie tego wymagałoby znajomości wszystkich etykiet, czyli
  przebiegu wstępnego.
