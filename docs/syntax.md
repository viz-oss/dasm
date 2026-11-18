# Składnia języka

Język DASM jest mały i celowo „asemblerowy”: program to lista linii, z których
każda jest etykietą, przypisaniem, wywołaniem, dyrektywą albo `return`.
Wcięcia nie mają znaczenia. Duże i małe litery **mają** znaczenie (poza
słowami kluczowymi, które są zapisane małymi literami).

## Komentarze i białe znaki

```asm
; komentarz
# komentarz
// komentarz
```

Wszystkie trzy formy działają do końca linii. Puste linie są ignorowane.
Spacje i tabulatory separują tokeny.

## Rejestry

Rejestr zapisuje się jako `rN`, gdzie `N` to nieujemna liczba całkowita:

```asm
r0 = 1
r1 = r0
r128 = 2
```

Rejestry są **wirtualne** — backend mapuje je na fizyczne rejestry, lokale
WASM albo komórki pamięci (zależnie od architektury). Nazwy `rN` są
zarezerwowane i nie mogą być użyte jako etykieta ani stała.

## Etykiety

```asm
start:
main:
pętla:
🚀:
```

Nazwa etykiety może zawierać litery Unicode, cyfry, `_` i emoji, ale nie może
zaczynać się od cyfry. Etykieta z dwukropkiem to osobny token, więc nie jest
podmieniana przez preprocesor. Duplikaty są odrzucane przez walidację symboli
(`label 'nazwa' defined twice`) albo przez backend podczas bezpośredniego
wywołania `Architecture.assembly()` (`Duplicate label: nazwa`).

## Przypisania

```asm
r0 = 1          ; stała liczba
r1 = 0x20       ; liczba szesnastkowa
r2 = -5         ; liczba ujemna
r3 = 1_000      ; separator tysięcy
r4 = r0         ; kopia rejestru
r5 = message    ; adres etykiety (Ptr)
message = r0    ; zapis rejestru pod adres symboliczny
[0xD020] = r0   ; zapis rejestru pod adres liczbowy
```

- Po lewej stronie może być rejestr (`rN`) albo adres (`nazwa` lub liczba).
- Po prawej: rejestr, liczba lub nazwa (traktowana jako wskaźnik/adres).
- Liczby w źródle: dziesiętne (z `_`), szesnastkowe `0x...` i ujemne.
  Literały binarne (`0b...`) i ósemkowe (`0o...`) nie są obsługiwane przez
  parser (działają tylko w wartościach `.set`).
- Obsługiwane formy zależą od backendu — patrz
  [architectures.md](architectures.md). Np. `mos6502` nie implementuje
  kopiowania rejestr→rejestr, a `wasm` nie obsługuje adresów etykiet.

## Funkcje, parametry i wywołania

Definicja z parametrami:

```asm
dodaj(a: r0, b: r1):
    r0 = 1
    r1 = 2
    return
```

- `a: r0` oznacza, że argument nazwany `a` zostanie powiązany z `r0`.
- Argumenty są nazwane, więc ich kolejność w wywołaniu nie ma znaczenia.
- `parse()` tworzy `Arg` z `reg=None`; `lang.symbols.resolve()` uzupełnia rejestr
  na podstawie definicji etykiety.
- Resolver zgłasza brakujące argumenty (`missing arguments [...]`), nieznane
  parametry, duplikaty argumentów i nieznane etykiety (`call: unknown label ...`).
- Etykieta może być zdefiniowana przed lub po wywołaniu.

Wywołania:

```asm
dodaj(a = 1, b = 2)
r0 = dodaj(a = 1, b = 2)
```

- Wynik wywołania (`r0 = ...`) jest zapisywany w AST, ale obecne backendy go
  nie obsługują.
- Argumenty przekazywane są przez rejestry parametrów; backend emituje
  odpowiednie instrukcje przed skokiem (np. `mos6502` ładuje immediates i
  wykonuje `JSR`).
- Argument może być liczbą, rejestrem albo nazwą (Ptr). Backend może
  obsługiwać tylko część tych form.

## `return` i `.exit`

```asm
return
return 5
.exit
```

- `return` kończy funkcję. `return <liczba>` przekazuje wartość w architekturach,
  które to obsługują (`wasm`); `mos6502` emituje tylko `RTS`.
- `.exit` to dyrektywa wyjścia z programu. `mos6502` emituje `RTS`, `wasm`
  `return`; pozostałe architektury rzucają `NotImplementedError`.

## Dyrektywy

Dyrektywy zaczynają się od kropki i są zapisane małymi literami. Każda musi wystąpić w osobnej linii.

| Dyrektywa | Argument | Znaczenie |
|---|---|---|
| `.start <etykieta>` | nazwa | punkt wejścia programu; duplikat jest błędem |
| `.exit` | brak | wyjście z programu |
| `.raw('ascii') '...'` | string | tekst ascii; parser tworzy `Raw`, ale obecne backendy nic nie emitują |
| `.raw('petcii') '...'` | string | tekst petcii (Commodore); parser tworzy `Raw`, ale obecne backendy nic nie emitują |
|  `.raw('utf-8') '...'`| string | tekst utf-8; parser tworzy `Raw`, ale obecne backendy nic nie emitują |
|  `.raw('utf-16') '...'`|  string|stekst utf-16; parser tworzy `Raw`, ale obecne backendy nic nie emitują  |
| `.raw` / `.raw(8)` | lista liczb | bajty (`Raw`, rozmiar 1) |
| `.raw(16)` | lista liczb | liczby 16-bitowe (`Raw`, rozmiar 2) |
| `.raw(32)` | lista liczb | liczby 32-bitowe (`Raw`, rozmiar 4) |
| `.raw(64)` | lista liczb | liczby 64-bitowe (`Raw`, rozmiar 8) |

```asm
.start main
.exit
.raw("ascii") "Hello"
.raw('utf-8') 'Dzień dobry'
.raw(8) 0x60, 0x01
.raw(16) 1, 2
```

Nieznana lub źle użyta dyrektywa daje `unknown or misused directive <nazwa>`.

## Stringi

Stringi są w podwójnych lub pojedynczych cudzysłowach i obsługują escape'y Pythona:

```asm
.raw("ascii") "Hello\n"
```

## Ograniczenia składni

- Brak operatorów arytmetycznych w źródle — `r0 + 2` nie jest obsługiwane.
- Brak etykiet lokalnych, sekcji, makr i warunkowej kompilacji.
- Brak wieloliniowych stringów.
- Brak typów i deklaracji zmiennych — wszystko jest rejestrem albo adresem.
- `return`, `rN` i nazwy dyrektyw są zarezerwowane; `return_value` jest już
  poprawną nazwą.
- Etykiety i nazwy są wrażliwe na wielkość liter (`Foo` ≠ `foo`).
- `parse()` odpowiada za składnię; walidacja symboli jest osobnym krokiem przez
  `lang.symbols.resolve(ast)`; CLI wykonuje ten krok przed assembly.
- Błędy resolvera (duplikaty etykiet, brak etykiety, brakujące argumenty,
  nieznane symbole) nie mają jeszcze numeru linii ani kolumny.
- `.start` jest sprawdzany przez parser tylko pod kątem formy dyrektywy; kontrolę,
  czy etykieta istnieje, wykonuje resolver.
