"""
Grammar Module

Contiene la gramática Lark para parsing de pseudocódigo.
"""

from pathlib import Path

GRAMMAR_FILE = Path(__file__).parent / "pseudocode.lark"

__all__ = ["GRAMMAR_FILE"]