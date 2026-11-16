"""Architecture: WebAssembly (WASM)

Minimal bytecode backend. Virtual registers rN are mapped to WASM locals,
so `r0 = 1` becomes `i32.const 1; local.set 0`.

WASM uses LEB128 immediates, therefore all numbers and local indices are
encoded with the helpers below. This module emits raw WASM opcodes for one
implicit function and closes its body with the structural `end` opcode.
Wrapping the stream into a valid .wasm module (header, type/function/code
sections) is done by `format.wasm`.
"""

from arch.base import Architecture
from lang.abstract import Int, Ptr


# Opcodes used by this backend.
OP_END = 0x0B
OP_RETURN = 0x0F
OP_LOCAL_GET = 0x20
OP_LOCAL_SET = 0x21
OP_I32_LOAD = 0x28
OP_I32_STORE = 0x36
OP_I32_CONST = 0x41

# memarg for a naturally aligned i32 access: align = 2, offset = 0.
MEMARG_I32 = [2, 0]


def uleb128(value: int) -> list[int]:
        """
        Encodes a non-negative integer into a list of bytes using unsigned LEB128 encoding.
        """
    """Encode a non-negative integer as unsigned LEB128."""
    assert value >= 0, f"ULEB128 requires a non-negative value: {value}"
    result: list[int] = []
    while True:
        byte = value & 0x7F  # Mask off the lower 7 bits to get the current byte
        value >>= 7
        if value:
            result.append(byte | 0x80)
        else:
            result.append(byte)
            return result


def sleb128(value: int) -> list[int]:
    """Encode a signed integer as signed LEB128."""
    result: list[int] = []
    while True:
        byte = value & 0x7F  # Mask off the lower 7 bits to get the current byte
        value >>= 7
        if (value == 0 and not (byte & 0x40)) or (value == -1 and (byte & 0x40)):
            result.append(byte)
            return result
        result.append(byte | 0x80)


class WasmArchitecture(Architecture):

    word_size = 1        # byte-oriented output
    endian = 'little'    # little endian
    entry_jump_size = 0  # WASM has no direct jump instruction

    # ASSEMBLY

    def assembly(self, ast, origin: int = 0,
                 start: str | None = None,
                 entry_jump: bool = False) -> list[int]:
        output = super().assembly(ast, origin, start, entry_jump)
        # The whole program is one implicit WASM function. Its body must
        # always be closed with the structural `end` opcode.
        output.append(OP_END)
        return output

    # Helpers

    def _address(self, ptr: Ptr) -> list[int]:
        """Emit an i32.const with a fixed memory address."""
        if not isinstance(ptr.target, Int):
            raise NotImplementedError(
                f"WASM label address relocation is not supported: {ptr.target}"
            )
        assert ptr.target.value >= 0, f"negative address: {ptr.target.value}"
        return [OP_I32_CONST, *sleb128(ptr.target.value)]

    # MOV

    def mov(self, instr) -> list[int]:
        if instr.to_reg():
            if instr.fr_int():
                return self._mov_int_reg(instr)
            if instr.fr_reg():
                return self._mov_reg_reg(instr)
            if instr.fr_ptr():
                return self._load(instr)
        elif instr.to_ptr():
            if instr.fr_reg():
                return self._store(instr)
        raise NotImplementedError(instr)

    def _mov_int_reg(self, instr) -> list[int]:
        return [
            OP_I32_CONST, *sleb128(instr.fr.value),
            OP_LOCAL_SET, *uleb128(instr.to.n),
        ]

    def _mov_reg_reg(self, instr) -> list[int]:
        return [
            OP_LOCAL_GET, *uleb128(instr.fr.n),
            OP_LOCAL_SET, *uleb128(instr.to.n),
        ]

    def _load(self, instr) -> list[int]:
        """rN = @address"""
        return [
            *self._address(instr.fr),
            OP_I32_LOAD, *MEMARG_I32,
            OP_LOCAL_SET, *uleb128(instr.to.n),
        ]

    def _store(self, instr) -> list[int]:
        """@address = rN"""
        return [
            *self._address(instr.to),
            OP_LOCAL_GET, *uleb128(instr.fr.n),
            OP_I32_STORE, *MEMARG_I32,
        ]

    # CALL

    def call(self, instr, offset: int = 0) -> list[int]:
        raise NotImplementedError(
            "WASM call requires function indices and a module wrapper"
        )

    # RET

    def ret(self, instr) -> list[int]:
        if instr.value is None:
            return [OP_RETURN]
        return [OP_I32_CONST, *sleb128(instr.value.value), OP_RETURN]

    # EXIT

    def exit(self, instr) -> list[int]:
        # `.exit` leaves the program/host and may appear anywhere. In a
        # single-function module `return` is the closest equivalent; the
        # structural function `end` is appended once by assembly().
        return [OP_RETURN]

    # JMP

    def jmp(self, target: str, offset: int = 0) -> list[int]:
        raise NotImplementedError(
            "WASM has no direct jump; use structured control flow"
        )


EXPORTS = WasmArchitecture
