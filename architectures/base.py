"""
Bazowa klasa dla modulow architektury.
Kazdy nowy modul architektury (np. alu8, cpu8) dziedziczy po Architecture
i implementuje jej metody / atrybuty.
"""

from abc import ABC, abstractmethod


class Architecture(ABC):
    """Interfejs modulu architektury."""

    # Nazwa uzywana w --arch
    name: str = "base"

    # Rozmiar slowa instrukcji w bitach (np. 8, 16)
    word_size: int = 8

    # Czy assembler ma wspierac etykiety / adresy (potrzebne dla CPU z JMP itp.)
    supports_labels: bool = False

    @abstractmethod
    def instruction_set(self) -> dict:
        """
        Zwraca slownik:
        {
            "MNEMONIC": {
                "opcode": int,          # wartosc liczbowa opcode
                "opcode_bits": int,     # liczba bitow opcode
                "operands": [...],      # lista typow operandow, np. ["reg4"], ["imm4"], []
            },
            ...
        }
        """
        raise NotImplementedError

    @abstractmethod
    def encode(self, mnemonic: str, operands: list[str], context: dict) -> int:
        """
        Koduje pojedyncza instrukcje do liczby calkowitej (word_size bitow).

        mnemonic: nazwa instrukcji, wielkimi literami
        operands: lista operandow jako stringi (po rozwiazaniu etykiet)
        context:  dodatkowe info, np. {"labels": {...}, "address": current_addr}
        """
        raise NotImplementedError

    def parse_operand(self, token: str, operand_type: str, labels: dict) -> int:
        """
        Domyslny parser operandu. Moze byc nadpisany przez konkretna architekture.
        Wspiera: liczby dziesietne, hex (0x..), binarne (0b..), etykiety (jesli supports_labels).
        """
        token = token.strip()

        if token in labels:
            return labels[token]

        if token.lower().startswith("0x"):
            return int(token, 16)
        if token.lower().startswith("0b"):
            return int(token, 2)

        # rejestr w formie R0, R1, ...
        if operand_type.startswith("reg") and token.upper().startswith("R"):
            return int(token[1:])

        return int(token)

    def max_operand_value(self, operand_type: str) -> int:
        """Maksymalna wartosc dla danego typu operandu (do walidacji)."""
        bits = self._operand_bits(operand_type)
        return (1 << bits) - 1

    @staticmethod
    def _operand_bits(operand_type: str) -> int:
        """Wyciaga liczbe bitow z typu operandu, np. 'reg4' -> 4, 'imm8' -> 8."""
        digits = "".join(c for c in operand_type if c.isdigit())
        if not digits:
            raise ValueError(f"Nie mozna ustalic liczby bitow dla typu '{operand_type}'")
        return int(digits)
