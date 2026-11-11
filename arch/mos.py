"""
Architecture: MOS 6502/6510 for C=64

Przesyłanie danych    
LDA, LDX, LDY
STA, STX, STY
Ładowanie danych z pamięci do rejestrów (Load) oraz zapisywanie zawartości rejestrów do pamięci (Store).

Operacje arytmetyczne    
ADC, SBC
Dodawanie z przeniesieniem (Add with Carry) oraz odejmowanie z pożyczką (Subtract with Borrow).

Operacje logiczne i bitowe
AND, ORA, EOR, BIT
Koniunkcja, alternatywa, alternatywa wykluczająca (XOR) oraz testowanie bitów.

Inkrementacja i dekrementacja    
INC, DEC
INX, INY, DEX, DEY
Zwiększanie lub zmniejszanie o 1 wartości w pamięci lub w rejestrach indeksowych X i Y.

Skoki bezwarunkowe i podprogramy
JMP, JSR, RTS
Skok pod wskazany adres (Jump), skok do podprogramu z zapamiętaniem adresu powrotu (Jump to Subroutine) oraz powrót z podprogramu (Return from Subroutine).

Skoki warunkowe (gałęzie)
BEQ, BNE, BMI, BPL, BCS, BCC
Skoki względne zależne od stanu flag (np. skok, jeśli wynik poprzedniej operacji wynosi zero – BEQ).

Operacje na stosie
PHA, PLA, PHP, PLP
Odkładanie (Push) i zdejmowanie (Pull) akumulatora lub rejestru flag ze stosu systemowego.

Sterowanie procesorem
NOP, SEC, CLC, SEI, CLI
Instrukcja pusta (No Operation), ustawianie lub czyszczenie flag (np. przeniesienia czy przerwań).
"""

from arch.base import Architecture


class MOSArchitecture(Architecture):

    def __init__(self):
        super().__init__()
        self.endian = 'little'

    def mov(self, instr) -> list[int]:
        if instr.to_reg():
            if instr.fr_int():
                assert 0 <= instr.fr.value < 255
                return self._lda_immediate(instr)
        elif instr.to_ptr():
            if instr.fr_reg():
                return self._sta_address(instr)
        raise NotImplementedError(instr)

    def _lda_immediate(self, instr) -> list[int]:
        return [0xA9, instr.fr.value]

    def _sta_address(self, instr) -> list[int]:
        address = instr.to.target.value
        assert isinstance(address, int)
        assert 0 <= address < 65535
        byte0, byte1 = address.to_bytes(2, byteorder=self.endian)
        return [0x8D, byte0, byte1]

    def call(self, instr) -> list[int]:
        return [0x4C, 0x0D, 0x08]


EXPORTS = MOSArchitecture
