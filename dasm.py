"""
Main launching script.
"""

__version__ = '2.0.2'

from pathlib import Path
import argparse, sys, importlib
from lang.syntax import parse
from lang.exceptions import DasmSyntaxError


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


def main(argv = None):
    parser = argparse.ArgumentParser(description=f"dasm v{__version__}")
    parser.add_argument(
        'source',
        help='input file .dasm'
    )
    parser.add_argument(
        '--arch',
        choices=['alu48', 'arm64', 'mos', 'wasm', 'x86'],
        default='arm64',
        help='output architecture'
    )
    parser.add_argument(
        '--format',
        choices=['bin', 'elf', 'hex', 'macho', 'prg'],
        default='macho',
        help='output format',
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

    print(f"dasm v{__version__}")
    source_text = source_path.read_text(encoding='utf-8')

    # Parse
    print("Parsing...", end='')
    try:
        ast = parse(source_text)
    except DasmSyntaxError as e:
        print('\n')
        print(f"{args.source}:{e.line if e.line else ''}:{e.col if e.col else ''}: syntax error\n{e}", file=sys.stderr)
        return 1
    print("OK")

    # Load architecture
    print("Architecture...", end='')
    arch = load_module('arch', args.arch)
    print(args.arch)

    # Assembly
    print("Assembly...", end='')
    words = arch.assembly(ast)
    print("OK")

    # Format output
    print("Format...", end='')
    format = load_module('format', args.format)
    output = format.output(words)
    print(args.format)

    # Save output file
    print("Output...", end='')
    output_name = args.output if args.output else source_path.name.replace('.dasm', '.' + format.ext)
    if not output_name.endswith('.' + format.ext): output_name += '.' + format.ext
    output_path = Path(output_name)
    with open(output_path, 'wb') as f:
        f.write(output)
        print(f'"{output_name}"')
    
    # Exit
    return 0


if __name__ == "__main__":
    sys.exit(main())
