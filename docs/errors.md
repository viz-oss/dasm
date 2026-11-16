# Błędy i mapowanie źródła

## `DasmSyntaxError`

Wszystkie błędy składni, preprocesora i importów są zgłaszane jako
`lang.exceptions.DasmSyntaxError`:

```python
DasmSyntaxError(
    line=None, col=None, expected=None, message='',
    file=None, map_columns=False, context=False,
)
```

| Pole | Znaczenie |
|---|---|
| `line`, `col` | pozycja 1-based (może być `None`) |
| `expected` | lista oczekiwanych tokenów (wyświetlana jako `Expected a or b`) |
| `message` | treść błędu; przy `context=True` zawiera też linię i `^` |
| `file` | plik źródłowy (jeśli już znany) |
| `map_columns` | czy kolumnę trzeba przetłumaczyć przez `ColumnMap` |
| `context` | czy odtworzyć kontekst z oryginalnej linii |

`str(error)` zwraca `Expected ...\n\n<message>` albo samo `message`.

## Skąd biorą się błędy

| Etap | Ustawia `line`/`col` | `map_columns` | `context` | `file` |
|---|---|---|---|---|
| parser (Lark `UnexpectedInput`) | tak | `True` | `True` | później |
| parser (`VisitError`, zły literał) | tak (jeśli token ma) | `True` | `False` | później |
| błędy semantyczne parsera | nie | `False` | `False` | później |
| preprocesor (`.set`, config) | zwykle tak | `False` | `False` | później |
| import (brak pliku, cykl, env) | tak | `False` | `False` | **tak** |

Błędy semantyczne parsera to m.in. `duplicate .start directive`,
`Label <nazwa> not found` i `Args mismatch in <nazwa>`. Nie mają jeszcze
numeru linii, więc w CLI pojawiają się z pustymi polami `:line:col:`.

## Potok relokacji

`dasm.py` robi:

```python
resolved = resolve_with_map(...)          # pliki + SourceMap
preprocessed = preprocess_with_map(...)   # .set + ColumnMap
ast = parse(preprocessed.text)
except DasmSyntaxError as e:
    e = source_map.relocate(e, preprocessed.column_maps)
```

- Błędy importu mają już `file`, więc `relocate()` ich nie zmienia.
- Błędy preprocesora i parsera mają wirtualne numery linii (po wklejeniu
  importów), które `SourceMap` tłumaczy na plik i linię.
- Kolumny parsera są tłumaczone przez `ColumnMap`, jeśli tekst został
  zmieniony przez `.set` (np. `X` → `1000`).

## `SourceMap`

`SourceMap(locations)` dostaje listę `SourceLocation(path, line)` dla kolejnych
wirtualnych linii. Kolejne linie z tego samego pliku i o kolejnych numerach są
łączone w `SourceSegment(start, end, path, line)`.

- `lookup(virtual_line)` zwraca `SourceLocation` albo `None` (poza zakresem),
- `original_line(location)` czyta oryginalny plik UTF-8 (z cache) i zwraca
  właściwą linię; przy błędzie odczytu lub poza zakresem — `None`,
- `relocate(error, column_maps=None)`:
  1. jeśli `error.file` jest ustawione albo `line is None` — zwraca błąd bez
     zmian,
  2. `lookup()`; brak lokalizacji — bez zmian,
  3. jeśli `map_columns` i jest `ColumnMap` — tłumaczy kolumnę,
  4. ustawia `file` i `line`,
  5. jeśli `context` — podmienia `message` na oryginalną linię z `^`
     (taby są rozwijane przy liczeniu pozycji kursora),
  6. odświeża `error.args`.

## `ColumnMap`

`ColumnMap` opisuje jedną linię jako listę `ColumnSegment(start, end, source,
fixed=False)`.

- brak segmentów → kolumna bez zmian (identity),
- kolumna przed pierwszym segmentem → bez zmian,
- `fixed=True` (podstawiona stała) → **każda** kolumna segmentu wskazuje na
  `source`, czyli na początek nazwy stałej,
- w przeciwnym razie `source + (processed_col - start)`.

Przykład: `.set X = 1000` i `r0 = X +` daje po podmianie `r0 = 1000 +`.
Błąd w kolumnie 7 (w `1000`) jest raportowany jako kolumna 6 (w `X`), a
kontekst pokazuje oryginalne `r0 = X +`.

## Wyświetlanie w CLI

```text
program.dasm:2:6: syntax error
Expected register or number

r0 = 
     ^
```

- Ścieżka jest pokazywana względem bieżącego katalogu (`_display_path`).
- Puste `line`/`col` dają `program.dasm::`.
- Komunikaty trafiają na `stderr`, a kod wyjścia to `1`.

## Znane ograniczenia

- Błędy semantyczne parsera nie mają pozycji.
- Błędy asemblacji (`Undefined label`, `Duplicate label`,
  `Address out of range`) i błędy backendów nie przechodzą przez relokację —
  są to wyjątki Pythona (`ValueError`, `NotImplementedError`, `AssertionError`).
- `ColumnMap` nie jest tworzony dla linii `.set` (jest pusta), bo linia i tak
  jest zastępowana pustą.
