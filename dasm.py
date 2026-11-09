"""
Main launching script.
"""

__version__ = '2.0.2'

from pathlib import Path
import argparse, sys, importlib
from syntax import parse, DasmSyntaxError
from arch.arm64 import Arm64Architecture # TODO: use load_module


def load_module(dir: str, name: str):
    """Dynamically loads the module from <dir>/<name>.py"""
    try:
        module = importlib.import_module(f"{dir}.{name}")
    except ModuleNotFoundError as e:
        raise DasmSyntaxError(
            f"Module '{dir}/{name}' not found "
        ) from e

    if not hasattr(module, "EXPORTS"):
        raise DasmSyntaxError(
            f"Module {dir}/{name}.py does not contain EXPORTS"
        )

    return module.EXPORTS()


def format_output(words: list[int], word_size: int, fmt: str) -> str:
    if fmt == 'bin':
        return '\n'.join(format(w, f"0{word_size}b") for w in words)
    if fmt == 'hex':
        hex_digits = (word_size + 3) // 4
        return '\n'.join(format(w, f"0{hex_digits}X") for w in words)
    if fmt == 'dec':
        return '\n'.join(str(w) for w in words)
    if fmt == 'logisim':
        # Format Logisim Evolution "v2.0 raw"
        hex_digits = (word_size + 3) // 4
        lines = ['v2.0 raw']
        lines.extend(format(w, f"0{hex_digits}x") for w in words)
        return '\n'.join(lines)
    raise AssemblerError(f"Unknown output format: {fmt}")


def write_bytes(words: list[int], word_size: int, path: Path):
    """Zapisuje slowa jako bajty/raw binary (do EEPROM programmer / .bin)."""
    byte_count = (word_size + 7) // 8
    with open(path, 'wb') as f:
        for w in words:
            f.write(w.to_bytes(byte_count, byteorder='big'))


def main(argv = None):
    parser = argparse.ArgumentParser(description=f"dasm v{__version__}")
    parser.add_argument(
        'source',
        help='input file .dasm'
    )
    parser.add_argument(
        '--arch',
        default='arm64',
        help='output architecture'
    )
    parser.add_argument(
        '--format',
        choices=['mach-o'],
        default='mach-o',
        help='output format (default: Mach-o)',
    )
    parser.add_argument(
        '-o', '--output',
        help='output file (default: <source name>.o)'
    )
    parser.add_argument(
        '-d', '--debug',
        help='debugging mode for the output file'
    )
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"File not found: {source_path}", file=sys.stderr)
        return 1

    source_text = source_path.read_text(encoding='utf-8')

    # Parse
    try:
        ast = parse(source_text)
    except DasmSyntaxError as e:
        print(f"{args.source}:{e.line if e.line else ''}:{e.col if e.col else ''}: syntax error\n{e}", file=sys.stderr)
        return 1

    # Load architecture
    """
    try:
        arch = load_module('arch', args.arch)
    except DasmSyntaxError as e:
        print(f"Architecture error: {e}", file=sys.stderr)
        return 1
    """
    arch = Arm64Architecture() # TODO: use load_module

    # Assembly
    words = arch.assembly(ast)

    # Format output
    #output = format_output(words, arch.word_size, args.format)

    # Save binary .o

    # Save additional debug .txt
    

    return 0


if __name__ == "__main__":
    sys.exit(main())
