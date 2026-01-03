"""
Tests del Semantic Analyzer
"""

import pytest
from app.core.parser import parse_pseudocode, SemanticAnalyzer
from app.core.exceptions import SemanticErrorException

class TestSemanticAnalyzer:
    """Tests del analizador semántico"""

    def test_valid_algorithm(self):
        """Test: Algoritmo válido sin errores"""
        code = """
        algorithm test(n)
        begin
            x ← 1
            for i ← 1 to n do
            begin
                x ← x + 1
            end
        end
        """
        ast = parse_pseudocode(code)
        analyzer = SemanticAnalyzer()

        result = analyzer.analyze(ast)
        assert result is True

    def test_parameter_usage(self):
        """Test: Uso de parámetros"""
        code = """
        algorithm sum(a, b)
        begin
            result ← a + b
            return result
        end
        """
        ast = parse_pseudocode(code)
        analyzer = SemanticAnalyzer()

        result = analyzer.analyze(ast)
        assert result is True

        # Verificar que los parámetros están en la tabla de símbolos
        assert "a" in analyzer.symbol_table
        assert "b" in analyzer.symbol_table
        assert analyzer.symbol_table["a"].is_parameter

    def test_recursive_function(self):
        """Test: Detección de recursión"""
        code = """
        algorithm fibonacci(n)
        begin
            if (n <= 1) then
            begin
                return n
            end
            return fibonacci(n - 1) + fibonacci(n - 2)
        end
        """
        ast = parse_pseudocode(code)
        analyzer = SemanticAnalyzer()

        analyzer.analyze(ast)

        # Verificar que se detectó la recursión
        assert analyzer.is_recursive("fibonacci")

    def test_array_parameter(self):
        """Test: Parámetros array"""
        code = """
        algorithm bubbleSort(A[n])
        begin
            for i ← 1 to n do
            begin
                temp ← A[i]
            end
        end
        """
        ast = parse_pseudocode(code)
        analyzer = SemanticAnalyzer()

        analyzer.analyze(ast)

        # Verificar que el array está registrado
        assert "A" in analyzer.symbol_table
        assert analyzer.symbol_table["A"].is_array