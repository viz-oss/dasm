"""
Main launching script.
"""

__version__ = '2.0.2'

from pathlib import Path
import argparse, os, sys
from lang.preprocess import preprocess_with_map
from lang.imports import resolve_with_map
from lang.syntax import parse
from lang.exceptions import DasmSyntaxError
import bootstrap.settings
from bootstrap.modules import load_module


def _display_path(path):
    """Show a source path relative to the current working directory."""
    if path is None:
        return None
    file_path = Path(path)
    if not file_path.is_absolute():
        return str(file_path)
    return os.path.relpath(file_path, Path.cwd())


def main(argv = None):
    # Commandline parser
    parser = argparse.ArgumentParser(description=f"dasm v{__version__}")
    parser.add_argument(
        'source',
        help='input file .dasm'
    )
    parser.add_argument(
        '--arch',
        choices=['alu48', 'arm64', 'mos', 'wasm', 'x86'],
        help='output architecture'
    )
    parser.add_argument(
        '--format',
        choices=['bin', 'elf', 'hex', 'macho', 'prg'],
        help='output format',
    )
    parser.add_argument(
        '-o', '--output',
        help='output file (default: <source name>.o)'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='debugging mode for the output file'
    )
    args = parser.parse_args(argv)
    
    # Header
    print(f"dasm v{__version__}")

    # Settings in *.toml
    settings = bootstrap.settings.load_all()
    
    # Options
    options = {
        # Defaults
        'arch': 'arm64',
        'format': 'macho',
        'debug' : False,
        # Read from *.toml
        **settings.get('options', {}),
        # Commandline
        'source': args.source,
        'output': args.output,
    }
    # Commandline
    if args.arch: options['arch'] = args.arch
    if args.format: options['format'] = args.format
    if args.debug: options['debug'] = args.debug
    
    # Read source file
    source_path = Path(options['source'])
    if not source_path.exists():
        print(f"File not found: {source_path}", file=sys.stderr)
        return 1
    source_text = source_path.read_text(encoding='utf-8')

    # Preprocess/Parse
    print("Parsing...", end='')
    source_map = None
    column_maps = None
    try:
        resolved = resolve_with_map(source_text, settings['env'], settings['paths'], source_path)
        source_map = resolved.source_map
        preprocessed = preprocess_with_map(resolved.text, settings['env'])
        column_maps = preprocessed.column_maps
        ast = parse(preprocessed.text)
    except DasmSyntaxError as e:
        if source_map is not None:
            e = source_map.relocate(e, column_maps)
        error_file = _display_path(e.file) if e.file else options['source']
        line = e.line if e.line is not None else ''
        col = e.col if e.col is not None else ''
        print('\n')
        print(f"{error_file}:{line}:{col}: syntax error\n{e}", file=sys.stderr)
        return 1
    print("OK")

    # Load architecture
    print("Architecture...", end='')
    arch = load_module('arch', options['arch'])
    print(options['arch'])

    # Assembly
    print("Assembly...", end='')
    words = arch.assembly(ast)
    print("OK")

    # Format output
    print("Format...", end='')
    format = load_module('format', options['format'])
    output = format.output(words)
    print(options['format'])

    # Save output file
    print("Output...", end='')
    output_name = options['output'] if options['output'] else source_path.name.replace('.dasm', '.' + format.ext)
    if not output_name.endswith('.' + format.ext): output_name += '.' + format.ext
    output_path = Path(output_name)
    with open(output_path, 'wb') as f:
        f.write(output)
        print(f'"{output_name}"')
    
    # Exit
    return 0


if __name__ == "__main__":
    sys.exit(main())
