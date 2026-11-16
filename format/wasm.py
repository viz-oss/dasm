"""Format: WebAssembly binary module

Wraps the flat opcode stream produced by `arch.wasm` into a complete
WebAssembly module: magic/version, type, function, optional memory,
export and code sections.

The architecture owns the function body, including its final `end`
opcode. This format only adds the module envelope and section lengths.
"""

from format.base import Format


MAGIC = b'\x00asm'
VERSION = b'\x01\x00\x00\x00'

OP_UNREACHABLE = 0x00
OP_END = 0x0B
OP_RETURN = 0x0F
OP_CALL = 0x10
OP_LOCAL_GET = 0x20
OP_LOCAL_SET = 0x21
OP_I32_LOAD = 0x28
OP_I32_STORE = 0x36
OP_I32_CONST = 0x41

VALTYPE_I32 = 0x7F
EXPORT_FUNC = 0x00
EXPORT_MEMORY = 0x02


def _uleb128(value: int) -> bytes:
    """Encode a non-negative integer as unsigned LEB128."""
    assert value >= 0, f"ULEB128 requires a non-negative value: {value}"
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            result.append(byte | 0x80)
        else:
            result.append(byte)
            return bytes(result)


def _read_uleb128(data, pos: int) -> tuple[int, int]:
    """Read an unsigned LEB128 value, returning (value, next position)."""
    result = 0
    shift = 0
    while True:
        if pos >= len(data):
            raise ValueError("unexpected end of WASM code")
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return result, pos
        shift += 7


def _skip_leb128(data, pos: int) -> int:
    """Skip a signed or unsigned LEB128 value."""
    while True:
        if pos >= len(data):
            raise ValueError("unexpected end of WASM code")
        byte = data[pos]
        pos += 1
        if not (byte & 0x80):
            return pos


def _vec(items: list[bytes]) -> bytes:
    """Encode a WASM vector."""
    return _uleb128(len(items)) + b''.join(items)


def _name(text: str) -> bytes:
    """Encode a WASM name."""
    data = text.encode('utf-8')
    return _uleb128(len(data)) + data


def _section(section_id: int, payload: bytes) -> bytes:
    return bytes([section_id]) + _uleb128(len(payload)) + payload


class FormatWasm(Format):

    # File extension
    ext = 'wasm'

    # Minimum linear memory size in 64 KiB pages.
    memory_pages = 1

    # Name of the exported entry function.
    export_name = 'main'

    def _scan(self, words: list[int]) -> tuple[int, bool, bool]:
        """Find the largest local index, memory usage and the final end."""
        max_local = -1
        uses_memory = False
        pos = 0
        last_opcode = None
        last_opcode_pos = 0

        while pos < len(words):
            last_opcode_pos = pos
            opcode = words[pos]
            last_opcode = opcode
            pos += 1

            if opcode == OP_I32_CONST:
                pos = _skip_leb128(words, pos)
            elif opcode in (OP_LOCAL_GET, OP_LOCAL_SET):
                index, pos = _read_uleb128(words, pos)
                max_local = max(max_local, index)
            elif opcode in (OP_I32_LOAD, OP_I32_STORE):
                uses_memory = True
                _, pos = _read_uleb128(words, pos)  # alignment
                _, pos = _read_uleb128(words, pos)  # offset
            elif opcode == OP_CALL:
                _, pos = _read_uleb128(words, pos)
            elif opcode in (OP_END, OP_RETURN, OP_UNREACHABLE):
                pass
            else:
                raise ValueError(
                    f"unsupported WASM opcode 0x{opcode:02X} "
                    f"at offset {last_opcode_pos}"
                )

        ends_with_end = (
            last_opcode == OP_END and last_opcode_pos + 1 == len(words)
        )
        return max_local + 1, uses_memory, ends_with_end

    def _type_section(self) -> bytes:
        # One function type: () -> ()
        functype = bytes([0x60, 0x00, 0x00])
        return _section(1, _vec([functype]))

    def _function_section(self) -> bytes:
        # One function using type index 0.
        return _section(3, _vec([_uleb128(0)]))

    def _memory_section(self) -> bytes:
        # One memory with a minimum size and no maximum.
        memtype = bytes([0x00]) + _uleb128(self.memory_pages)
        return _section(5, _vec([memtype]))

    def _export(self, name: str, kind: int, index: int) -> bytes:
        return _name(name) + bytes([kind]) + _uleb128(index)

    def _export_section(self, uses_memory: bool) -> bytes:
        exports = [self._export(self.export_name, EXPORT_FUNC, 0)]
        if uses_memory:
            exports.append(self._export('memory', EXPORT_MEMORY, 0))
        return _section(7, _vec(exports))

    def _code_section(self, words: list[int], local_count: int) -> bytes:
        if local_count:
            # One group: local_count locals of type i32.
            locals_vec = _vec([
                _uleb128(local_count) + bytes([VALTYPE_I32])
            ])
        else:
            locals_vec = _vec([])

        body = locals_vec + bytes(words)
        code = _uleb128(len(body)) + body
        return _section(10, _vec([code]))

    def output(self, words: list[int], entry: int | None = None) -> bytes:
        words = list(words)
        if entry not in (None, 0):
            raise ValueError(
                "WASM can only start at the beginning of the function; "
                f"entry offset {entry} is not supported yet"
            )
        local_count, uses_memory, ends_with_end = self._scan(words)
        if not ends_with_end:
            raise ValueError(
                "WASM code must end with the function end opcode (0x0B)"
            )

        sections = [
            self._type_section(),
            self._function_section(),
        ]
        if uses_memory:
            sections.append(self._memory_section())
        sections.append(self._export_section(uses_memory))
        sections.append(self._code_section(words, local_count))
        return MAGIC + VERSION + b''.join(sections)


EXPORTS = FormatWasm
