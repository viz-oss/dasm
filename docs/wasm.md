# WebAssembly (`wasm`)

Backend WASM składa się z dwóch modułów:

- `arch/wasm.py` — generuje strumień opcodów jednej funkcji,
- `format/wasm.py` — opakowuje strumień w kompletny moduł `.wasm`.

## Model

- Cały program to **jedna funkcja** bez parametrów i bez wyniku (`() -> ()`).
- Rejestr `rN` jest lokalem WASM o indeksie `N`.
- Brak stosu wywołań, etykiet, skoków i danych statycznych.
- Architektura zawsze dopisuje na końcu `end` (`0x0B`).
- `word_size = 1`, `endian = 'little'`, `entry_jump_size = 0`.

## Instrukcje architektury

| Źródło | Emitowane opcody |
|---|---|
| `rN = <liczba>` | `i32.const <sleb128>` + `local.set <uleb128 N>` |
| `rN = rM` | `local.get <uleb128 M>` + `local.set <uleb128 N>` |
| `rN = @<adres>` | `i32.const <adres>` + `i32.load 2 0` + `local.set N` |
| `@<adres> = rN` | `i32.const <adres>` + `local.get N` + `i32.store 2 0` |
| `return` | `return` (`0x0F`) |
| `return <liczba>` | `i32.const <liczba>` + `return` |
| `.exit` | `return` |

- `@<adres>` musi być literałem (`Ptr(Int(...))`), nie etykietą; adres musi
  być nieujemny. Etykieta daje `NotImplementedError`.
- `call` i `jmp` dają `NotImplementedError` (brak indeksów funkcji i skoków).
- `memarg` jest stały: `align = 2`, `offset = 0`.

### Opcody używane przez architekturę

| Stała | Wartość |
|---|---|
| `OP_END` | `0x0B` |
| `OP_RETURN` | `0x0F` |
| `OP_LOCAL_GET` | `0x20` |
| `OP_LOCAL_SET` | `0x21` |
| `OP_I32_LOAD` | `0x28` |
| `OP_I32_STORE` | `0x36` |
| `OP_I32_CONST` | `0x41` |

Liczby całkowite są kodowane jako LEB128: `uleb128()` dla nieujemnych,
`sleb128()` dla znaków.

## Format modułu

`FormatWasm.output(words)`:

1. odrzuca `entry` inne niż `None`/`0`,
2. skanuje strumień (`_scan`), aby znaleźć:
   - największy indeks lokalu (`max_local`),
   - użycie pamięci (`i32.load`/`i32.store`),
   - czy strumień kończy się `end`,
3. buduje sekcje:
   - **type (1)**: jeden typ `() -> ()`,
   - **function (3)**: jedna funkcja typu 0,
   - **memory (5)**: tylko przy użyciu pamięci; `[min = memory_pages]`
     bez maksimum,
   - **export (7)**: funkcja `main` (indeks 0) oraz `memory` (indeks 0),
     jeśli pamięć jest używana,
   - **code (10)**: deklaracja `max_local + 1` lokali typu `i32`
     (jedna grupa) + strumień opcodów.

Atrybuty klasy:

| Atrybut | Domyślnie | Znaczenie |
|---|---|---|
| `ext` | `wasm` | rozszerzenie pliku |
| `origin` | `0` | adres bazowy |
| `entry_jump` | `False` | brak skoku wejściowego |
| `memory_pages` | `1` | minimalna liczba stron pamięci (64 KiB) |
| `export_name` | `main` | nazwa eksportowanej funkcji |

### Skanowanie i obsługiwane opcody

`_scan` akceptuje wyłącznie:

| Opcode | Dodatkowe dane |
|---|---|
| `0x00` (`unreachable`) | brak |
| `0x0B` (`end`) | brak |
| `0x0F` (`return`) | brak |
| `0x10` (`call`) | `uleb128` indeks funkcji |
| `0x20`, `0x21` (`local.get/set`) | `uleb128` indeks lokalu |
| `0x28`, `0x36` (`i32.load/store`) | `uleb128` align + `uleb128` offset |
| `0x41` (`i32.const`) | `sleb128` wartość |

Inny opcode daje
`ValueError: unsupported WASM opcode 0xXX at offset N`.
Ucięte LEB128 daje `ValueError: unexpected end of WASM code`.
Strumień bez końcowego `end` daje `ValueError: ... end opcode ...`.

## Przykłady

Pusty program:

```python
arch.assembly([])  # [0x0B]
```

Moduł ma sekcje `[1, 3, 7, 10]`; code section to `01 02 00 0B`
(jedna funkcja, 2 bajty ciała: brak lokali + `end`).

`r0 = 1`:

```python
arch.assembly([Mov(Reg(0), Int(1))])
# [0x41, 0x01, 0x21, 0x00, 0x0B]
```

Code section: `01 08 01 01 7F 41 01 21 00 0B` (jeden lokal `i32`, potem ciało).

`@100 = r0`:

```python
arch.assembly([Mov(Ptr(Int(100)), Reg(0))])
# [0x41, 0xE4, 0x00, 0x20, 0x00, 0x36, 0x02, 0x00, 0x0B]
```

Moduł dostaje sekcję memory `01 00 01` oraz eksport `memory`.

Pełny przykład z CLI:

```bash
printf 'r0 = 1\n' > prog.dasm
python3 dasm.py prog.dasm --arch wasm --format wasm
```

## Ograniczenia

- Brak wywołań funkcji (`call`), skoków i etykiet.
- Brak danych statycznych i sekcji data.
- Tylko jeden typ funkcji i jedna funkcja.
- Pamięć jest eksportowana, ale nie ma funkcji startowej poza `main`.
- Brak obsługi wielu wyników, parametrów i typów innych niż `i32`.
- `.start` działa tylko dla etykiety pod offsetem 0 (format odrzuca inne
  `entry`).
