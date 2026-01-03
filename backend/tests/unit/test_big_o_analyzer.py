"""
Tests para Big O Analyzer

Tests unitarios para el analizador de complejidad Big O.
"""

import pytest
from app.core.parser import parse_pseudocode
from app.core.analyzer.complexity.big_o_analyzer import BigOAnalyzer


class TestBigOAnalyzer:
    """Tests del analizador Big O"""
    
    def test_constant_time(self):
        """Test: O(1)"""
        code = """
        algorithm constant()
        begin
            x ← 1
        end
        """
        ast = parse_pseudocode(code)
        analyzer = BigOAnalyzer()
        result = analyzer.analyze(ast)
        
        assert "O(1)" in str(result)
    
    def test_linear_time(self):
        """Test: O(n)"""
        code = """
        algorithm linear(n)
        begin
            for i ← 1 to n do
            begin
                x ← x + 1
            end
        end
        """
        ast = parse_pseudocode(code)
        analyzer = BigOAnalyzer()
        result = analyzer.analyze(ast)
        
        assert "O(n)" in str(result)
    
    def test_quadratic_time(self):
        """Test: O(n^2)"""
        code = """
        algorithm quadratic(n)
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
        analyzer = BigOAnalyzer()
        result = analyzer.analyze(ast)
        
        assert "n^2" in str(result) or "n * n" in str(result)