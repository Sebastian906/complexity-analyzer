"""Tests para ExecutionCounter."""

import pytest
from app.core.parser.pseudocode_parser import PseudocodeParser
from app.core.analyzer.execution_counter import ExecutionCounter, count_executions

@pytest.fixture
def parser():
    return PseudocodeParser()

@pytest.fixture
def counter():
    return ExecutionCounter()

class TestExecutionCounterBasic:
    """Tests básicos de conteo."""
    
    def test_simple_assignment(self, parser, counter):
        """Asignación simple = O(1)."""
        code = """
        algorithm simple()
        begin
            x := 5
        end
        """
        ast = parser.parse(code)
        result = counter.count(ast, code)
        
        assert result["dominant"] == "O(1)"
    
    def test_single_for_loop(self, parser, counter):
        """Un for loop = O(n)."""
        code = """
        algorithm linear(n)
        begin
            for i := 1 to n do
            begin
                x := i
            end
        end
        """
        ast = parser.parse(code)
        result = counter.count(ast, code)
        
        assert result["dominant"] == "O(n)"
    
    def test_nested_for_loops(self, parser, counter):
        """Dos for anidados = O(n²)."""
        code = """
        algorithm quadratic(n)
        begin
            for i := 1 to n do
            begin
                for j := 1 to n do
                begin
                    x := i + j
                end
            end
        end
        """
        ast = parser.parse(code)
        result = counter.count(ast, code)
        
        assert result["dominant"] == "O(n²)"

class TestExecutionCounterLoops:
    """Tests de loops."""
    
    def test_triple_nested_loops(self, parser, counter):
        """Tres for anidados = O(n³)."""
        code = """
        algorithm cubic(n)
        begin
            for i := 1 to n do
            begin
                for j := 1 to n do
                begin
                    for k := 1 to n do
                    begin
                        x := 1
                    end
                end
            end
        end
        """
        ast = parser.parse(code)
        result = counter.count(ast, code)
        
        assert result["dominant"] == "O(n³)"
    
    def test_while_with_division(self, parser, counter):
        """While con división = O(log n)."""
        code = """
        algorithm logarithmic(n)
        begin
            x := n
            while (x > 1) do
            begin
                x := x / 2
            end
        end
        """
        ast = parser.parse(code)
        result = counter.count(ast, code)
        
        assert result["dominant"] == "O(log n)"

class TestExecutionCounterOutput:
    """Tests de formato de salida."""
    
    def test_output_structure(self, parser, counter):
        """El resultado tiene la estructura correcta."""
        code = """
        algorithm test()
        begin
            x := 1
        end
        """
        ast = parser.parse(code)
        result = counter.count(ast, code)
        
        assert "lines" in result
        assert "dominant" in result
        assert "total" in result

class TestConvenienceFunction:
    """Tests de la función de conveniencia."""
    
    def test_count_executions_function(self, parser):
        """La función count_executions funciona."""
        code = """
        algorithm test()
        begin
            x := 1
        end
        """
        ast = parser.parse(code)
        result = count_executions(ast, code)
        
        assert result["dominant"] == "O(1)"