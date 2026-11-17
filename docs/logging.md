# Logowanie

DASM ma wbudowany system logów oparty na module `logging` z biblioteki
standardowej. Implementacja znajduje się w `utils/log.py`, a logi włącza się
argumentem startowym `-l`/`--log`.

## Argument `--log`

| Forma | Efekt |
|---|---|
| brak argumentu | logi są wyłączone (domyślnie) |
| `-l`, `--log` | loguje wszystkie grupy (`*`) |
| `-l GRUPA`, `--log GRUPA` | loguje tylko wskazane grupy |
| `-l GRUPA1+GRUPA2` | kilka grup rozdzielonych znakiem `+` |

```bash
python3 dasm.py program.dasm --arch mos6502 --format prg
python3 dasm.py program.dasm --arch mos6502 --format prg --log
python3 dasm.py program.dasm --arch mos6502 --format prg --log lang
python3 dasm.py program.dasm --arch mos6502 --format prg --log lang.preprocess
```

Ponieważ `--log` przyjmuje opcjonalną wartość, źródło podawaj przed flagą
(`... --log lang`) albo użyj `--log=lang`. Samo `-l` na końcu polecenia
loguje wszystko.

### Grupy

Grupą jest pierwszy człon nazwy loggera, czyli nazwa pakietu, a pełna nazwa
loggera też może być użyta jako filtr:

| Filtr | Co loguje |
|---|---|
| `lang` | wszystkie moduły w `lang/` (`lang.syntax`, `lang.preprocess`, …) |
| `lang.preprocess` | tylko preprocesor |
| `lang+utils` | moduły z `lang/` i `utils/` |
| `*` | wszystko (to samo co `-l` bez wartości) |

Nieznana grupa nie jest błędem — po prostu nic nie pasuje i nie pojawia się
żaden log. Filtr dopasowuje pełną nazwę loggera (`record.name`) albo jej
pierwszy człon.

## Format i miejsce wyjścia

Logi trafiają na **stdout** przez `StreamHandler` dołączony do loggera
głównego. Każdy wpis ma postać:

```
[%(name)s] %(message)s
```

np. dla źródła:

```asm
.set BORDER = 0xD020
0xD020 = BORDER
```

log wygląda tak (linia przed i po podmianie, `.set` nie jest logowany):

```
dasm v2.0.2
Parsing...[lang.preprocess] 2: 0xD020 = BORDER
[lang.preprocess] 2: 0xD020 = 53280
[lang.preprocess] 3:
```

Linie bez zmian są logowane raz, a linie po podmianie stałych dwa razy.

Poziom loggera głównego i handlera to `DEBUG`, więc `logger.debug()`,
`logger.info()` i pozostałe poziomy przechodzą do filtra grup. Filtr decyduje
wyłącznie o tym, *które* wpisy są pokazywane, a nie o ich poziomie.

Ponieważ logi i komunikaty etapów (`Parsing...`, `Assembly...OK`) idą na
stdout, a błędy składni na stderr, kolejność w terminalu może się przeplatać.
W potokach stdout jest buforowany, dlatego logi mogą pojawić się po
komunikacie błędu.

## `utils/log.py`

Moduł udostępnia:

| Element | Znaczenie |
|---|---|
| `setup(groups_arg)` | konfiguruje logger główny i dodaje handler z filtrem; wywoływane raz w `dasm.py` przed nagłówkiem wersji |
| `LogGroupFilter(allowed_groups)` | filtr wpisów według nazwy loggera; `None` blokuje wszystko, `{'*'}` przepuszcza wszystko |
| `red(s)`, `green(s)`, `gray(s)` | pomocnicze kolorowanie tekstu (ANSI) |

`setup()` przyjmuje surowy ciąg z CLI i zamienia `A+B` na zbiór grup. Bez
argumentu zbiór jest pusty, więc domyślnie nic nie jest logowane.

Funkcje `red()`, `green()` i `gray()` dodają kody ANSI tylko wtedy, gdy
`sys.stdout.isatty()` jest prawdziwe, więc w potokach i plikach tekst
pozostaje czysty. Preprocesor używa `red()` dla linii przed podmianą stałych
i `green()` dla linii wynikowej (patrz
[preprocess_set.md](preprocess_set.md)).

## Dodawanie logów w nowym module

Wystarczy użyć standardowego loggera z nazwą modułu — nie trzeba tworzyć
własnego handlera ani konfiguracji:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("szczegóły")
logger.info("krok działania")
```

Logger o nazwie `lang.mojmodul` będzie widoczny dla `--log lang`,
`--log lang.mojmodul` i `--log` bez wartości. Grupy nie trzeba nigdzie
rejestrować.

## `--log` a `-d/--debug`

To niezależne opcje:

- `-l`/`--log` włącza diagnostykę samego asemblera na stdout,
- `-d`/`--debug` ustawia `debug = True` w opcjach przekazywanych do
  backendów i nie wpływa na logi.
