"""
Tests del Módulo de Ecuaciones de Recurrencia

Tests completos para RecurrenceBuilder, RecurrenceSolver y Analyzers.
"""

import pytest
from app.core.parser import parse_pseudocode
from app.core.analyzer.recurrence import (
    RecurrenceBuilder,
    RecurrenceSolver,
    RecurrenceForm,
    SolutionMethod,
    build_recurrence_equations,
    solve_recurrence,
    analyze_temporal_complexity,
    analyze_spatial_complexity
)

class TestRecurrenceBuilder:
    """Tests del constructor de ecuaciones"""

    def test_build_linear_recursion(self):
        """Test: Construir T(n) para recursión lineal"""
        code = """
        algorithm factorial(n)
        begin
            if (n <= 1) then
            begin
                return 1
            end
            return n * factorial(n - 1)
        end
        """
        ast = parse_pseudocode(code)
        builder = RecurrenceBuilder()

        temporal_eq = builder.build_temporal_recurrence(ast, "factorial")

        assert temporal_eq is not None
        assert temporal_eq.is_recursive
        assert temporal_eq.recursion_pattern == "linear"

    def test_build_binary_recursion(self):
        """Test: Construir T(n) para recursión binaria"""
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
        builder = RecurrenceBuilder()

        temporal_eq = builder.build_temporal_recurrence(ast, "fibonacci")

        assert temporal_eq is not None
        assert temporal_eq.is_recursive
        assert temporal_eq.recursion_pattern == "binary"

    def test_build_divide_and_conquer(self):
        """Test: Construir T(n) para divide y conquista"""
        code = """
        algorithm mergeSort(n)
        begin
            if (n > 1) then
            begin
                mid ← n / 2
                call mergeSort(mid)
                call mergeSort(n - mid)
            end
        end
        """
        ast = parse_pseudocode(code)
        builder = RecurrenceBuilder()

        temporal_eq = builder.build_temporal_recurrence(ast, "mergeSort")

        assert temporal_eq is not None
        assert temporal_eq.is_recursive
        assert temporal_eq.recursion_pattern == "binary"

    def test_non_recursive_algorithm(self):
        """Test: Algoritmo no recursivo no genera ecuación"""
        code = """
        algorithm linearSearch(A[n], x)
        begin
            for i ← 1 to n do
            begin
                if (A[i] = x) then
                begin
                    return i
                end
            end
            return -1
        end
        """
        ast = parse_pseudocode(code)
        builder = RecurrenceBuilder()

        temporal_eq = builder.build_temporal_recurrence(ast, "linearSearch")

        assert temporal_eq is None

    def test_build_spatial_recurrence(self):
        """Test: Construir S(n) para recursión"""
        code = """
        algorithm factorial(n)
        begin
            if (n <= 1) then
            begin
                return 1
            end
            return n * factorial(n - 1)
        end
        """
        ast = parse_pseudocode(code)
        builder = RecurrenceBuilder()

        spatial_eq = builder.build_spatial_recurrence(ast, "factorial")

        assert spatial_eq is not None
        assert spatial_eq.is_recursive
        assert spatial_eq.recurrence_type == "spatial"

class TestRecurrenceSolver:
    """Tests del solver de ecuaciones"""

    def test_detect_form_f0(self):
        """Test: Detectar forma F0"""
        solver = RecurrenceSolver()
        pattern = solver._detect_form("T(n) = T(n/2) + 1")

        assert pattern is not None
        assert pattern.form == RecurrenceForm.F0
        assert pattern.b == 2

    def test_detect_form_f1(self):
        """Test: Detectar forma F1"""
        solver = RecurrenceSolver()
        pattern = solver._detect_form("T(n) = 2T(n/2) + n")

        assert pattern is not None
        assert pattern.form == RecurrenceForm.F1
        assert pattern.a == 2
        assert pattern.b == 2

    def test_detect_form_f4(self):
        """Test: Detectar forma F4"""
        solver = RecurrenceSolver()
        pattern = solver._detect_form("T(n) = T(n-1) + 1")

        assert pattern is not None
        assert pattern.form == RecurrenceForm.F4
        assert pattern.b == 1

    def test_detect_form_f5(self):
        """Test: Detectar forma F5"""
        solver = RecurrenceSolver()
        pattern = solver._detect_form("T(n) = 2T(n-1) + 1")

        assert pattern is not None
        assert pattern.form == RecurrenceForm.F5
        assert pattern.a == 2
        assert pattern.b == 1

    def test_master_theorem_case1(self):
        """Test: Teorema Maestro Caso 1"""
        result = solve_recurrence(
            "T(n) = 2T(n/2) + 1",
            method=SolutionMethod.MASTER_THEOREM
        )

        assert result.complexity == "n^1.00"  # log_2(2) = 1
        assert result.method_used == SolutionMethod.MASTER_THEOREM

    def test_master_theorem_case2(self):
        """Test: Teorema Maestro Caso 2"""
        result = solve_recurrence(
            "T(n) = 2T(n/2) + n",
            method=SolutionMethod.MASTER_THEOREM
        )

        assert "log" in result.complexity.lower()
        assert result.method_used == SolutionMethod.MASTER_THEOREM

    def test_master_theorem_case3(self):
        """Test: Teorema Maestro Caso 3"""
        result = solve_recurrence(
            "T(n) = 2T(n/2) + n^2",
            method=SolutionMethod.MASTER_THEOREM
        )

        assert "n^2" in result.complexity or "n²" in result.complexity
        assert result.method_used == SolutionMethod.MASTER_THEOREM

    def test_iteration_method_f0(self):
        """Test: Método de iteración F0"""
        result = solve_recurrence(
            "T(n) = T(n/2) + 1",
            method=SolutionMethod.ITERATION
        )

        assert result.method_used == SolutionMethod.ITERATION
        assert len(result.steps) > 0

    def test_iteration_method_f4(self):
        """Test: Método de iteración F4"""
        result = solve_recurrence(
            "T(n) = T(n-1) + 1",
            method=SolutionMethod.ITERATION
        )

        assert result.complexity == "n"
        assert result.method_used == SolutionMethod.ITERATION

    def test_recursion_tree_method(self):
        """Test: Método de árbol de recursión"""
        result = solve_recurrence(
            "T(n) = 2T(n/2) + n",
            method=SolutionMethod.RECURSION_TREE
        )

        assert result.method_used == SolutionMethod.RECURSION_TREE
        assert len(result.steps) > 0

    def test_characteristic_equation_f4(self):
        """Test: Ecuación característica F4"""
        result = solve_recurrence(
            "T(n) = T(n-1) + 1",
            method=SolutionMethod.CHARACTERISTIC_EQUATION
        )

        assert result.complexity == "n"
        assert result.method_used == SolutionMethod.CHARACTERISTIC_EQUATION

    def test_characteristic_equation_f5(self):
        """Test: Ecuación característica F5"""
        result = solve_recurrence(
            "T(n) = 2T(n-1) + 1",
            method=SolutionMethod.CHARACTERISTIC_EQUATION
        )

        assert "2^n" in result.complexity
        assert result.method_used == SolutionMethod.CHARACTERISTIC_EQUATION

    def test_smart_substitution(self):
        """Test: Sustitución inteligente"""
        result = solve_recurrence(
            "T(n) = 2T(n/2) + n",
            method=SolutionMethod.SMART_SUBSTITUTION
        )

        assert result.method_used == SolutionMethod.SMART_SUBSTITUTION
        assert len(result.steps) > 0

    def test_automatic_method_selection(self):
        """Test: Selección automática del mejor método"""
        result = solve_recurrence("T(n) = 2T(n/2) + n")

        # Debe elegir Master Theorem (más directo para F1)
        assert result.method_used == SolutionMethod.MASTER_THEOREM

    def test_alternative_methods(self):
        """Test: Métodos alternativos disponibles"""
        result = solve_recurrence("T(n) = 2T(n/2) + n")

        assert len(result.alternative_methods) > 0
        assert SolutionMethod.RECURSION_TREE in result.alternative_methods

class TestTemporalComplexityAnalyzer:
    """Tests del analizador temporal"""

    def test_analyze_recursive_algorithm(self):
        """Test: Analizar algoritmo recursivo"""
        code = """
        algorithm factorial(n)
        begin
            if (n <= 1) then
            begin
                return 1
            end
            return n * factorial(n - 1)
        end
        """
        ast = parse_pseudocode(code)

        t_n, _ = build_recurrence_equations(ast, "factorial")
        result = analyze_temporal_complexity(t_n)

        assert result.is_recursive
        assert result.recurrence_equation is not None
        assert "O(" in result.big_o

    def test_analyze_non_recursive_algorithm(self):
        """Test: Analizar algoritmo no recursivo"""
        result = analyze_temporal_complexity(None, fallback="n")

        assert not result.is_recursive
        assert result.big_o == "O(n)"
        assert result.solution is None

    def test_get_complexity_insights(self):
        """Test: Obtener insights de complejidad"""
        from app.core.analyzer.recurrence.temporal_complexity import TemporalComplexityAnalyzer

        analyzer = TemporalComplexityAnalyzer()
        insights = analyzer.get_complexity_insights("n log n")

        assert insights["class"] == "Linealítmica"
        assert "examples" in insights

class TestSpatialComplexityAnalyzer:
    """Tests del analizador espacial"""

    def test_analyze_recursive_space(self):
        """Test: Analizar espacio recursivo"""
        code = """
        algorithm factorial(n)
        begin
            if (n <= 1) then
            begin
                return 1
            end
            return n * factorial(n - 1)
        end
        """
        ast = parse_pseudocode(code)

        _, s_n = build_recurrence_equations(ast, "factorial")
        result = analyze_spatial_complexity(s_n, input_space="1", auxiliary_space="1")

        assert result.is_recursive
        assert "O(" in result.space_complexity

    def test_analyze_non_recursive_space(self):
        """Test: Analizar espacio no recursivo"""
        result = analyze_spatial_complexity(
            None,
            input_space="n",
            auxiliary_space="1"
        )

        assert not result.is_recursive
        assert result.space_complexity == "O(n)"

    def test_space_breakdown(self):
        """Test: Desglose de espacio"""
        from app.core.analyzer.recurrence.spatial_complexity import SpatialComplexityAnalyzer

        code = """
        algorithm test(A[n])
        begin
            for i ← 1 to n do
            begin
                x ← x + 1
            end
        end
        """
        ast = parse_pseudocode(code)

        _, s_n = build_recurrence_equations(ast, "test")
        result = analyze_spatial_complexity(s_n, input_space="n", auxiliary_space="1")

        analyzer = SpatialComplexityAnalyzer()
        breakdown = analyzer.get_space_breakdown(result)

        assert "total" in breakdown
        assert "components" in breakdown

class TestIntegration:
    """Tests de integración completos"""

    def test_full_analysis_merge_sort(self):
        """Test: Análisis completo de Merge Sort"""
        code = """
        algorithm mergeSort(n)
        begin
            if (n > 1) then
            begin
                mid ← n / 2
                call mergeSort(mid)
                call mergeSort(n - mid)
            end
        end
        """
        ast = parse_pseudocode(code)

        # Construir ecuaciones
        t_n, s_n = build_recurrence_equations(ast, "mergeSort")

        assert t_n is not None
        assert t_n.is_recursive
        assert t_n.recursion_pattern == "binary"

        # Resolver T(n)
        temporal_result = analyze_temporal_complexity(t_n)

        assert temporal_result.is_recursive
        assert temporal_result.solution is not None

        # Resolver S(n)
        if s_n:
            spatial_result = analyze_spatial_complexity(s_n, input_space="n", auxiliary_space="n")
            assert spatial_result.is_recursive

    def test_full_analysis_fibonacci(self):
        """Test: Análisis completo de Fibonacci"""
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

        t_n, s_n = build_recurrence_equations(ast, "fibonacci")

        assert t_n is not None
        assert t_n.recursion_pattern == "binary"

        temporal_result = analyze_temporal_complexity(t_n)

        # Fibonacci debería ser exponencial
        assert temporal_result.is_recursive

    def test_compare_methods(self):
        """Test: Comparar resultados de diferentes métodos"""
        from app.core.analyzer.recurrence.temporal_complexity import TemporalComplexityAnalyzer

        analyzer = TemporalComplexityAnalyzer()
        comparison = analyzer.compare_methods("T(n) = 2T(n/2) + n")

        assert len(comparison) > 0
        assert "teorema_maestro" in comparison or "master_theorem" in comparison

class TestEdgeCases:
    """Tests de casos extremos"""

    def test_invalid_equation_format(self):
        """Test: Formato de ecuación inválido"""
        solver = RecurrenceSolver()
        result = solver.solve("invalid equation")

        assert result.complexity == "unknown"
        assert not result.is_exact

    def test_unsupported_form(self):
        """Test: Forma no soportada"""
        # F3 (múltiple división) es más compleja
        result = solve_recurrence("T(n) = T(n/2) + T(n/3) + T(n/4) + n")

        # Debe poder resolverla con algún método (sustitución)
        assert result is not None

    def test_deeply_nested_recursion(self):
        """Test: Recursión profundamente anidada"""
        code = """
        algorithm complex(n)
        begin
            if (n > 0) then
            begin
                call complex(n - 1)
                call complex(n - 1)
                call complex(n - 1)
            end
        end
        """
        ast = parse_pseudocode(code)

        t_n, _ = build_recurrence_equations(ast, "complex")

        # Debería detectar recursión múltiple
        assert t_n is not None
        assert t_n.recursion_pattern == "multiple"

# Fixtures

@pytest.fixture
def sample_equations():
    """Fixture con ecuaciones de ejemplo"""
    return {
        "f0": "T(n) = T(n/2) + 1",
        "f1": "T(n) = 2T(n/2) + n",
        "f2": "T(n) = T(n/2) + T(n/3) + n",
        "f4": "T(n) = T(n-1) + 1",
        "f5": "T(n) = 2T(n-1) + 1",
        "f6": "T(n) = T(n-1) + T(n-2) + 1"
    }

@pytest.fixture
def sample_algorithms():
    """Fixture con algoritmos de ejemplo"""
    return {
        "factorial": """
algorithm factorial(n)
begin
    if n <= 1 then
        return 1
    return n * factorial(n - 1)
end
        """,
        "fibonacci": """
algorithm fibonacci(n)
begin
    if n <= 1 then
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
end
        """,
        "binary_search": """
algorithm binarySearch(A[n], x, left, right)
begin
    if left > right then
        return -1

    mid ← (left + right) / 2

    if A[mid] = x then
        return mid

    if A[mid] > x then
        return binarySearch(A, x, left, mid - 1)
    else
        return binarySearch(A, x, mid + 1, right)
end
        """
    }

# Tests parametrizados

@pytest.mark.parametrize("equation,expected_form", [
    ("T(n) = T(n/2) + 1", RecurrenceForm.F0),
    ("T(n) = 2T(n/2) + n", RecurrenceForm.F1),
    ("T(n) = T(n-1) + 1", RecurrenceForm.F4),
    ("T(n) = 2T(n-1) + 1", RecurrenceForm.F5),
])
def test_detect_various_forms(equation, expected_form):
    """Test parametrizado: Detectar varias formas"""
    solver = RecurrenceSolver()
    pattern = solver._detect_form(equation)

    assert pattern is not None
    assert pattern.form == expected_form