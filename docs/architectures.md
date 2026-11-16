# Architektury

Architektura to backend, który zamienia AST na listę słów wyjściowych
(`list[int]`). Wybór odbywa się przez `--arch NAME` lub `[dasm.options].arch`.

## Interfejs `Architecture`

Plik `arch/base.py` definiuje klasę abstrakcyjną:

```python
class Architecture(ABC):
    word_size: int = 1          # rozmiar jednego elementu wyjścia w bajtach
    entry_jump_size: int = 0    # rozmiar skoku wejściowego (0 = brak)
    endian: Literal['little', 'big'] | None = None

    def assembly(self, ast, origin=0, start=None, entry_jump=False) -> list[int]
    def mov(self, instr) -> list[int]
    def call(self, instr, offset=0) -> list[int]
    def ret(self, instr) -> list[int]
    def exit(self, instr) -> list[int]
    def jmp(self, target: str, offset=0) -> list[int]
```

Metody `mov`, `call`, `ret`, `exit`, `jmp` są abstrakcyjne i muszą być
zaimplementowane (mogą na razie rzucać `NotImplementedError`). Bazowa
`assembly()` obsługuje cały przebieg:

1. czyści `labels`, `relocations`, `origin`, `start`, `entry`,
2. jeśli podano `start` i `entry_jump=True`, emitowany jest `jmp(start)` na
   początku (etykiety są automatycznie przesunięte o `entry_jump_size`),
3. dla każdej instrukcji AST:
   - `Start` — no-op (punkt wejścia obsługuje CLI/format),
   - `Label` — zapis przesunięcia w bajtach (`len(output) * word_size`),
   - `Mov` → `mov()`,
   - `Call` → `call(instr, offset=len(output))`,
   - `Bytes` → `bytes()` (domyślnie jeden bajt na wartość, `size` ignorowany),
   - `Text` → `text()` (domyślnie nic nie emituje),
   - `Return` → `ret()`,
   - `Exit` → `exit()`,
4. `apply_relocations()` uzupełnia adresy etykiet i sprawdza zakres,
5. jeśli podano `start`, ustawia `entry = origin + labels[start]`.

`Relocation(offset, target, size=2, endian='little')` wskazuje indeks w
`output`, od którego trzeba wpisać adres etykiety. `apply_relocations()`
zgłasza `Undefined label: ...` oraz `Address out of range for ...`.

> Relokacje są zaprojektowane dla architektur jednobajtowych (`word_size = 1`).
> Dla `arm64` (`word_size = 4`) nie są jeszcze używane.

## Stan backendów

### `arm64` — `arch/arm64.py`

- `word_size = 4`, `endian = 'little'`, brak skoku wejściowego.
- `mov`:
  - `rN = <liczba 0..0xFFFF>` → jedna instrukcja `MOVZ` (32-bitowe słowo),
  - `rN = rM` → `_orr`, na razie `NotImplementedError`,
  - `rN = @...`, `@... = rN` → `NotImplementedError`.
- `_movz(rd, imm16, hw=0, x=True)` buduje słowo `MOVZ`; waliduje `rd` w
  `0..31`, `imm16` w `0..0xFFFF`, `hw` w `0..3`.
- `call`, `ret`, `exit`, `jmp` → `NotImplementedError`.
- Etykiety są rejestrowane przez bazową `assembly()`, ale nic ich nie używa.

### `mos6502` — `arch/mos6502.py`

Rejestry wirtualne: `r0` = A, `r1` = X, `r2` = Y.

- `word_size = 1`, `endian = 'little'`, `entry_jump_size = 3` (`JMP $xxxx`).
- `mov`:
  - `r0/r1/r2 = <0..255>` → `LDA/LDX/LDY #imm` (`0xA9`, `0xA2`, `0xA0`),
  - `@<0..65535> = r0/r1/r2` → `STA/STX/STY absolute` (`0x8D`, `0x8E`, `0x8C`),
  - pozostałe kombinacje → `NotImplementedError`.
- `call`: argumenty są emitowane przez `mov()` do rejestrów z `Arg._reg`,
  następnie `JSR` (`0x20`) z 2-bajtową relokacją adresu. Obecnie działają
  argumenty będące liczbami; rejestry i wskaźniki wymagają trybów `mov`,
  których jeszcze nie ma.
- `ret` i `exit` → `RTS` (`0x60`).
- `jmp` → `JMP` (`0x4C`) z relokacją 2-bajtową.
- Tryby adresowania `zero page`, `absolute,X/Y`, `indirect` itd. mają metody
  pomocnicze, ale wszystkie rzucają `NotImplementedError`.
- `_absolute16()` przyjmuje wyłącznie `int` w `0..65535`.

### `wasm` — `arch/wasm.py`

- `word_size = 1`, `endian = 'little'`, brak skoku wejściowego.
- Jedna domyślna funkcja i jeden lokal na rejestr: `rN` → lokal `N`.
- Emituje opcody WASM i zawsze zamyka ciało funkcji opcodem `end` (`0x0B`).
- Szczegóły: [wasm.md](wasm.md).

### `x86` — `arch/x86.py`

Placeholder (sam docstring). Brak `EXPORTS`, więc `--arch x86` kończy się
`DasmSyntaxError: Module arch/x86.py does not contain EXPORTS`.

### `alu48` — `arch/alu48.py`

Legacy, oznaczony jako `DEPRECATED / IGNORE`. Nie dziedziczy po
`Architecture`, ma własny interfejs (`instruction_set`, `encode`,
`microcode_table`) i eksportuje `ARCHITECTURE`, a nie `EXPORTS`. Nie działa
przez CLI ani przez `load_module()`.

## Dodawanie architektury

1. Utwórz `arch/nazwa.py` z klasą dziedziczącą po `arch.base.Architecture`.
2. Ustaw `word_size`, `endian` i ewentualnie `entry_jump_size`.
3. Zaimplementuj `mov`, `call`, `ret`, `exit`, `jmp` (stuby z
   `NotImplementedError` są dopuszczalne).
4. Na końcu pliku dodaj `EXPORTS = TwojaKlasa` (musi być callable).
5. Dodaj `nazwa` do `choices` w `--arch` w `dasm.py`.
6. Dopisz testy do `tests/test_arch_nazwa.py`.

Więcej: [development.md](development.md).
