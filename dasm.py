"""
Main launching script.
"""

__version__ = '2.0.2'

from pathlib import Path
import argparse, sys, importlib
from syntax import parse, DasmSyntaxError


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
        choices=['bin', 'elf', 'hex', 'macho'],
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

    source_text = source_path.read_text(encoding='utf-8')

    # Parse
    try:
        ast = parse(source_text)
    except DasmSyntaxError as e:
        print(f"{args.source}:{e.line if e.line else ''}:{e.col if e.col else ''}: syntax error\n{e}", file=sys.stderr)
        return 1

    # Load architecture
    arch = load_module('arch', args.arch)

    # Assembly
    words = arch.assembly(ast)

    # Format output
    format = load_module('format', args.format)
    output = format.output(words)

    # Save output file
    output_name = args.output if args.output else source_path.name.replace('.dasm', '.' + format.ext)
    if not output_name.endswith('.' + format.ext): output_name += '.' + format.ext
    output_path = Path(output_name)
    with open(output_path, 'wb') as f:
        f.write(output)
    
    # Exit
    return 0


if __name__ == "__main__":
    sys.exit(main())
