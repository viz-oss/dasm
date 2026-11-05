#!/usr/bin/env python3
"""
Glowny silnik uruchamiający kompilator.
"""

__version__ = '0.2.0'

#import importlib
#import re
#import sys
from pathlib import Path
import argparse, sys

from arch import wasm


def main(argv = None):
    parser = argparse.ArgumentParser(description = f"Dasm v{__version__}")
    parser.add_argument(
        'source', help = 'input file .dasm'
    )
    parser.add_argument(
        '--arch', required = True, help = 'output architecture'
    )
    parser.add_argument(
        '-o', '--output', help='output file (default: <source name>.<arch extension>)'
    )
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"File not found: {source_path}", file = sys.stderr)
        return 1

    source_lines = source_path.read_text(encoding = 'utf-8').splitlines()
    print(source_lines)



# DEPRECATED ------------------------------------------------------------------------------

COMMENT_CHAR = ";"


class AssemblerError(Exception):
    def __init__(self, message: str, line_no: int = None):
        self.line_no = line_no
        if line_no is not None:
            message = f"Linia {line_no}: {message}"
        super().__init__(message)


def load_architecture(arch_name: str):
    """Dynamicznie laduje modul architektury z architectures/<arch_name>.py"""
    try:
        module = importlib.import_module(f"architectures.{arch_name}")
    except ModuleNotFoundError as e:
        raise AssemblerError(
            f"Nie znaleziono modulu architektury '{arch_name}' "
            f"(szukano architectures/{arch_name}.py)"
        ) from e

    if not hasattr(module, "ARCHITECTURE"):
        raise AssemblerError(
            f"Modul architectures/{arch_name}.py nie eksportuje zmiennej ARCHITECTURE"
        )

    return module.ARCHITECTURE()


def strip_comment(line: str) -> str:
    if COMMENT_CHAR in line:
        line = line[: line.index(COMMENT_CHAR)]
    return line.strip()


def tokenize_line(line: str):
    """
    Zwraca (label_or_None, mnemonic_or_None, [operands...])
    Etykiety musza koncyc sie ':' i byc na poczatku linii, np.:
        LOOP: ADD 5
    lub w osobnej linii:
        LOOP:
            ADD 5
    """
    label = None

    label_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
    if label_match:
        label = label_match.group(1)
        line = label_match.group(2).strip()

    if not line:
        return label, None, []

    parts = re.split(r"[,\s]+", line)
    mnemonic = parts[0].upper()
    operands = [p for p in parts[1:] if p]

    return label, mnemonic, operands


def assemble(source_lines: list[str], arch) -> list[int]:
    """
    Dwuprzebiegowy assembler.
    Zwraca liste zakodowanych slow (int), jedno na instrukcje.
    """

    # ---------- PRZEBIEG 1: zbierz etykiety ----------
    labels = {}
    address = 0
    parsed_lines = []  # (line_no, label, mnemonic, operands)

    for line_no, raw_line in enumerate(source_lines, start=1):
        line = strip_comment(raw_line)
        if not line:
            continue

        label, mnemonic, operands = tokenize_line(line)

        if label is not None:
            if not arch.supports_labels:
                raise AssemblerError(
                    f"Architektura '{arch.name}' nie wspiera etykiet ('{label}:')",
                    line_no,
                )
            if label in labels:
                raise AssemblerError(f"Etykieta '{label}' zdefiniowana wielokrotnie", line_no)
            labels[label] = address

        if mnemonic is not None:
            parsed_lines.append((line_no, label, mnemonic, operands))
            address += 1

    # ---------- PRZEBIEG 2: koduj instrukcje ----------
    instruction_set = arch.instruction_set()
    output_words = []

    for idx, (line_no, label, mnemonic, operands) in enumerate(parsed_lines):
        if mnemonic not in instruction_set:
            raise AssemblerError(f"Nieznana instrukcja '{mnemonic}'", line_no)

        spec = instruction_set[mnemonic]
        expected_operand_count = len(spec["operands"])

        # Dla architektur z opcjonalnymi operandami (np. Cn override) tolerujemy
        # wiecej operandow niz w specyfikacji - walidacja konkretna jest w arch.encode()
        if len(operands) < expected_operand_count and expected_operand_count > 0:
            # sprawdzamy tylko minimalna liczbe - arch.encode rzuci blad jesli naprawde za malo
            pass

        context = {"labels": labels, "address": idx}

        try:
            word = arch.encode(mnemonic, operands, context)
        except ValueError as e:
            raise AssemblerError(str(e), line_no) from e

        if word < 0 or word >= (1 << arch.word_size):
            raise AssemblerError(
                f"Zakodowane slowo {word} przekracza word_size={arch.word_size} bitow",
                line_no,
            )

        output_words.append(word)

    return output_words


def format_output(words: list[int], word_size: int, fmt: str) -> str:
    if fmt == "bin":
        return "\n".join(format(w, f"0{word_size}b") for w in words)
    if fmt == "hex":
        hex_digits = (word_size + 3) // 4
        return "\n".join(format(w, f"0{hex_digits}X") for w in words)
    if fmt == "dec":
        return "\n".join(str(w) for w in words)
    if fmt == "logisim":
        # Format Logisim Evolution "v2.0 raw"
        hex_digits = (word_size + 3) // 4
        lines = ["v2.0 raw"]
        lines.extend(format(w, f"0{hex_digits}x") for w in words)
        return "\n".join(lines)
    raise AssemblerError(f"Nieznany format wyjsciowy: {fmt}")


def write_bytes(words: list[int], word_size: int, path: Path):
    """Zapisuje slowa jako bajty/raw binary (do EEPROM programmer / .bin)."""
    byte_count = (word_size + 7) // 8
    with open(path, "wb") as f:
        for w in words:
            f.write(w.to_bytes(byte_count, byteorder="big"))


def main_old(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Modularny assembler dla wlasnych ALU/CPU")
    parser.add_argument("source", help="plik wejsciowy .asm")
    parser.add_argument(
        "--arch", required=True, help="nazwa modulu architektury (np. alu4)"
    )
    parser.add_argument("-o", "--output", help="plik wyjsciowy (domyslnie: stdout)")
    parser.add_argument(
        "--format",
        choices=["bin", "hex", "dec", "logisim", "raw"],
        default="bin",
        help="format wyjsciowy (domyslnie: bin = tekstowy 0/1)",
    )
    parser.add_argument(
        "--microcode",
        action="store_true",
        help="wypisz tabele mikrokodu dekodera (jesli architektura ja udostepnia) i zakoncz",
    )

    args = parser.parse_args(argv)

    try:
        arch = load_architecture(args.arch)
    except AssemblerError as e:
        print(f"Blad assemblera: {e}", file=sys.stderr)
        return 1

    if args.microcode:
        if not hasattr(arch, "microcode_table"):
            print(f"Architektura '{arch.name}' nie udostepnia tabeli mikrokodu.", file=sys.stderr)
            return 1
        table = arch.microcode_table()
        print(f"{'Opcode':<8}{'Mnemonik':<8}{'Dane (bin)':<12}{'Dane (hex)'}")
        for row in table:
            print(f"{row['opcode']:03b}     {row['mnemonic']:<8}{row['data_bin']:<12}{row['data_hex']}")
        return 0

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Plik nie istnieje: {source_path}", file=sys.stderr)
        return 1

    source_lines = source_path.read_text(encoding="utf-8").splitlines()

    try:
        words = assemble(source_lines, arch)
    except AssemblerError as e:
        print(f"Blad assemblera: {e}", file=sys.stderr)
        return 1

    if args.format == "raw":
        if not args.output:
            print("Format 'raw' wymaga podania --output", file=sys.stderr)
            return 1
        write_bytes(words, arch.word_size, Path(args.output))
        print(f"Zapisano {len(words)} slow ({arch.word_size}-bit) do {args.output}")
        return 0

    output_text = format_output(words, arch.word_size, args.format)

    if args.output:
        Path(args.output).write_text(output_text + "\n", encoding="utf-8")
        print(f"Zapisano {len(words)} slow do {args.output}")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
