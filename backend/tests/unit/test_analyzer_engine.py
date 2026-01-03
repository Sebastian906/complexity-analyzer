"""
Tests del Analyzer Engine
"""

import pytest
from app.core.parser import parse_pseudocode
from app.core.analyzer.analyzer_engine import AnalyzerEngine


class TestAnalyzerEngine:
    """Tests del motor de análisis"""
    
    def test_simple_algorithm(self):
        """Test: Algoritmo simple"""
        code = """
        algorithm simple()
        begin
            x ← 1
        end
        """
        ast = parse_pseudocode(code)
        engine = AnalyzerEngine()
        
        result = engine.analyze(ast)
        
        assert result.algorithm_name == "simple"
        assert "1" in result.big_o
    
    def test_linear_algorithm(self):
        """Test: Algoritmo lineal"""
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
        engine = AnalyzerEngine()
        
        result = engine.analyze(ast)
        
        assert "n" in result.big_o

    def test_line_by_line_analysis(self):
        """Test: Análisis línea por línea"""
        code = """
        algorithm test(n)
        begin
            x ← 1
            for i ← 1 to n do
            begin
                y ← y + 1
            end
        end
        """
        ast = parse_pseudocode(code)
        engine = AnalyzerEngine()

        result = engine.analyze(ast, analyze_line_by_line=True)

        assert result.line_by_line is not None
        assert len(result.line_by_line.lines) > 0