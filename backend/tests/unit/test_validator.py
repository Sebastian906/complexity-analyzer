"""
Tests del AST Validator
"""

import pytest
from app.core.parser import parse_pseudocode, ASTValidator

class TestASTValidator:
    """Tests del validador de AST"""

    def test_valid_ast(self):
        """Test: AST válido"""
        code = """
        algorithm test(n)
        begin
            x ← 1
        end
        """
        ast = parse_pseudocode(code)
        validator = ASTValidator()

        result = validator.validate(ast)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_nested_loops(self):
        """Test: Loops anidados"""
        code = """
        algorithm test(n)
        begin
            for i ← 1 to n do
            begin
                for j ← 1 to n do
                begin
                    x ← x + 1
                end
            end
        end
        """
        ast = parse_pseudocode(code)
        validator = ASTValidator()

        result = validator.validate(ast)

        assert result.is_valid
        stats = validator.get_stats()
        assert stats["max_depth"] > 1

    def test_max_depth_exceeded(self):
        """Test: Profundidad máxima excedida"""
        # Crear código con muchos niveles de anidación
        code = "algorithm test(n)\nbegin\n"
        for i in range(25):  # Más de 20 niveles
            code += "    " * i + "for i ← 1 to n do\n"
            code += "    " * i + "begin\n"
        code += "    " * 25 + "x ← 1\n"
        for i in range(24, -1, -1):
            code += "    " * i + "end\n"
        code += "end"

        ast = parse_pseudocode(code)
        validator = ASTValidator(max_depth=20)

        result = validator.validate(ast)

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_empty_blocks_warning(self):
        """Test: Bloques vacíos generan warnings"""
        code = """
        algorithm test(n)
        begin
            for i ← 1 to n do
            begin
            end
        end
        """
        ast = parse_pseudocode(code)
        validator = ASTValidator()

        result = validator.validate(ast)

        # Debería ser válido pero con warnings
        assert result.is_valid
        assert len(result.warnings) > 0