"""End-to-end test for the C=64 example with the .start directive."""

from pathlib import Path

from dasm import main


ROOT = Path(__file__).resolve().parents[1]


def test_c64_example_starts_at_main(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    output = tmp_path / "c64.prg"

    assert main(["examples/c64.dasm", "-o", str(output)]) == 0

    assert output.read_bytes() == bytes([
        0x01, 0x08,                          # load address 0x0801
        0x0B, 0x08,                          # next line
        0x0A, 0x00,                          # line 10
        0x9E, 0x32, 0x30, 0x36, 0x31,        # SYS 2061
        0x00,                                # end of line
        0x00, 0x00,                          # end of BASIC
        0x4C, 0x11, 0x08,                    # JMP main (0x0811)
        0x60,                                # exit: (0x0810)
        0xA9, 0x03,                          # main: r0 = VIC_CYAN
        0x8D, 0x20, 0xD0,                    # VIC_FRAME_COLOR = r0
        0xA9, 0x06,                          # r0 = VIC_BLUE
        0x8D, 0x21, 0xD0,                    # VIC_BG_COLOR = r0
        0x4C, 0x10, 0x08,                    # exit()
    ])
