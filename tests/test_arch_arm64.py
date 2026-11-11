"""Unit tests for an Arm64 architecture"""

import pytest
from lang.abstract import Label, Mov, Reg, Int
from arch.arm64 import Arm64Architecture


def test_arch_arm64():
    arch = Arm64Architecture()

    # r0 = 1
    ast = [Mov(to=Reg(n=0), fr=Int(value=1))]
    words = arch.assembly(ast)
    assert hex(words[0]) == '0xd2800020'
