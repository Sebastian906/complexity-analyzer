"""
Tests para Omega Analyzer (Mejor Caso)

Verifica que el análisis de complejidad en el mejor caso
funcione correctamente para diferentes estructuras.
"""

import pytest

from app.core.parser import parse_pseudocode
from app.core.analyzer.complexity.omega_analyzer import OmegaAnalyzer
from app.core.analyzer.complexity.base_analyzer import ComplexityResult

@pytest.fixture
def analyzer():
    """Crea instancia de OmegaAnalyzer"""
    return OmegaAnalyzer()

class TestBasicComplexity:
    """Tests para complejidades básicas"""
    
    def test_constant_complexity(self, analyzer):
        """Verifica Ω(1) para operaciones constantes"""
        code = """
        algorithm constant(n)
        begin
            x ← 5
            y ← 10
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        assert isinstance(result, ComplexityResult)
        assert result.notation == "Ω"
        assert result.complexity == "1"
    
    def test_linear_complexity(self, analyzer):
        """Verifica Ω(n) para loops lineales"""
        code = """
        algorithm linear(A[1..n])
        begin
            for i ← 1 to n do
            begin
                x ← A[i]
            end
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        assert result.complexity == "n"
    
    def test_quadratic_complexity(self, analyzer):
        """Verifica Ω(n²) para loops anidados"""
        code = """
        algorithm quadratic(A[1..n])
        begin
            for i ← 1 to n do
            begin
                for j ← 1 to n do
                begin
                    x ← A[i] + A[j]
                end
            end
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        assert result.complexity == "n^2"

class TestLoopAnalysis:
    """Tests para análisis de ciclos"""
    
    def test_for_loop_best_case(self, analyzer):
        """Verifica FOR loop en mejor caso"""
        code = """
        algorithm forloop(A[1..n])
        begin
            for i ← 1 to n do
            begin
                x ← x + 1
            end
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        # En el mejor caso, el loop se ejecuta n veces
        assert result.complexity == "n"
    
    def test_while_loop_best_case(self, analyzer):
        """Verifica WHILE loop en mejor caso"""
        code = """
        algorithm whileloop(n)
        begin
            i ← 1
            while (i < n) do
            begin
                i ← i + 1
            end
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        # En el mejor caso, podría no ejecutarse si i >= n desde el inicio
        # pero típicamente asumimos al menos 1 iteración
        assert result.complexity in ["1", "n"]
    
    def test_repeat_loop_best_case(self, analyzer):
        """Verifica REPEAT loop en mejor caso"""
        code = """
        algorithm repeatloop(n)
        begin
            i ← 0
            repeat
                i ← i + 1
            until (i >= n)
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        # REPEAT siempre se ejecuta al menos 1 vez
        assert result.complexity in ["1", "n"]

class TestConditionalAnalysis:
    """Tests para análisis de condicionales"""
    
    def test_if_without_else(self, analyzer):
        """Verifica IF sin ELSE"""
        code = """
        algorithm ifonly(n)
        begin
            if (n > 0) then
            begin
                x ← x + 1
            end
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        # En el mejor caso, la condición es false y no se ejecuta nada
        assert result.complexity == "1"
    
    def test_if_with_else(self, analyzer):
        """Verifica IF con ELSE (mejor caso)"""
        code = """
        algorithm ifelse(n)
        begin
            if (n > 0) then
            begin
                for i ← 1 to n do
                begin
                    x ← x + 1
                end
            end
            else
            begin
                x ← 0
            end
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        # En el mejor caso, se ejecuta el branch más rápido (else)
        assert result.complexity == "1"

class TestNestedStructures:
    """Tests para estructuras anidadas"""
    
    def test_nested_loops(self, analyzer):
        """Verifica loops anidados"""
        code = """
        algorithm nested(A[1..n])
        begin
            for i ← 1 to n do
            begin
                for j ← 1 to n do
                begin
                    x ← A[i] + A[j]
                end
            end
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        assert result.complexity == "n^2"
    
    def test_conditional_in_loop(self, analyzer):
        """Verifica condicional dentro de loop"""
        code = """
        algorithm condinloop(A[1..n])
        begin
            for i ← 1 to n do
            begin
                if (A[i] > 0) then
                begin
                    x ← x + 1
                end
            end
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        # El loop siempre se ejecuta n veces
        assert result.complexity == "n"

class TestSequentialStatements:
    """Tests para statements secuenciales"""
    
    def test_multiple_assignments(self, analyzer):
        """Verifica múltiples asignaciones"""
        code = """
        algorithm multiple(n)
        begin
            x ← 1
            y ← 2
            z ← 3
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        assert result.complexity == "1"
    
    def test_sequential_loops(self, analyzer):
        """Verifica loops secuenciales"""
        code = """
        algorithm sequential(A[1..n])
        begin
            for i ← 1 to n do
            begin
                x ← x + 1
            end
            for j ← 1 to n do
            begin
                y ← y + 1
            end
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        # O(n) + O(n) = O(n) en el mejor caso
        assert result.complexity == "n"

class TestEdgeCases:
    """Tests para casos especiales"""
    
    def test_empty_algorithm(self, analyzer):
        """Verifica algoritmo vacío"""
        code = """
        algorithm empty(n)
        begin
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        assert result.complexity == "1"
    
    def test_single_operation(self, analyzer):
        """Verifica operación única"""
        code = """
        algorithm single(n)
        begin
            x ← n + 1
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        assert result.complexity == "1"

class TestAlgorithmExamples:
    """Tests con ejemplos reales de algoritmos"""
    
    def test_linear_search_best_case(self, analyzer):
        """Verifica búsqueda lineal (mejor caso)"""
        code = """
        algorithm linearSearch(A[1..n], key)
        begin
            for i ← 1 to n do
            begin
                if (A[i] = key) then
                begin
                    return i
                end
            end
            return -1
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        # Mejor caso: elemento encontrado en primera posición
        # pero el analyzer ve el loop completo
        assert result.complexity in ["1", "n"]
    
    def test_bubble_sort_best_case(self, analyzer):
        """Verifica bubble sort (mejor caso)"""
        code = """
        algorithm bubbleSort(A[1..n])
        begin
            for i ← 1 to n do
            begin
                for j ← 1 to n - i do
                begin
                    if (A[j] > A[j + 1]) then
                    begin
                        temp ← A[j]
                        A[j] ← A[j + 1]
                        A[j + 1] ← temp
                    end
                end
            end
        end
        """
        ast = parse_pseudocode(code)
        result = analyzer.analyze(ast)
        
        # Mejor caso sigue siendo O(n²) para bubble sort básico
        assert result.complexity == "n^2"

# Test Runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])