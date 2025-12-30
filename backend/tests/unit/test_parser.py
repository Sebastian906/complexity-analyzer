"""
Tests Unitarios del Parser

Tests exhaustivos para el parser de pseudocódigo.
"""

import pytest

from app.core.exceptions import (
    ParserException,
    SyntaxErrorException,
)
from app.core.parser.pseudocode_parser import PseudocodeParser
from app.core.parser.ast_nodes import (
    AlgorithmNode,
    ForLoopNode,
    WhileLoopNode,
    RepeatLoopNode,
    IfStatementNode,
    AssignmentNode,
    CallStatementNode,
    BinaryOpNode,
    LiteralNode,
)

class TestParserBasic:
    """Tests básicos del parser"""

    @pytest.fixture
    def parser(self):
        """Fixture: instancia del parser"""
        return PseudocodeParser()

    def test_parser_initialization(self, parser):
        """Test: parser se inicializa correctamente"""
        assert parser is not None
        assert parser.parser is not None
        assert parser.ast_builder is not None

    def test_simple_algorithm(self, parser):
        """Test: parsear algoritmo simple"""
        code = """
        algorithm test(n)
        begin
            x ← 1
        end
        """

        ast = parser.parse(code)

        assert ast is not None
        assert ast.algorithm is not None
        assert ast.algorithm.name == "test"
        assert len(ast.algorithm.parameters) == 1
        assert ast.algorithm.parameters[0].name == "n"

    def test_empty_algorithm(self, parser):
        """Test: algoritmo vacío"""
        code = """
        algorithm empty()
        begin
        end
        """

        ast = parser.parse(code)

        assert ast.algorithm.name == "empty"
        assert len(ast.algorithm.parameters) == 0
        assert len(ast.algorithm.body.statements) == 0

class TestParserLoops:
    """Tests de estructuras de ciclos"""

    @pytest.fixture
    def parser(self):
        return PseudocodeParser()

    def test_for_loop(self, parser):
        """Test: ciclo FOR"""
        code = """
        algorithm test(n)
        begin
            for i ← 1 to n do
            begin
                x ← x + 1
            end
        end
        """

        ast = parser.parse(code)
        statements = ast.algorithm.body.statements

        assert len(statements) == 1
        assert isinstance(statements[0], ForLoopNode)
        assert statements[0].variable == "i"

    def test_while_loop(self, parser):
        """Test: ciclo WHILE"""
        code = """
        algorithm test(n)
        begin
            while (n > 0) do
            begin
                n ← n - 1
            end
        end
        """

        ast = parser.parse(code)
        statements = ast.algorithm.body.statements

        assert len(statements) == 1
        assert isinstance(statements[0], WhileLoopNode)

    def test_repeat_loop(self, parser):
        """Test: ciclo REPEAT"""
        code = """
        algorithm test(n)
        begin
            repeat
                n ← n - 1
            until (n = 0)
        end
        """

        ast = parser.parse(code)
        statements = ast.algorithm.body.statements

        assert len(statements) == 1
        assert isinstance(statements[0], RepeatLoopNode)

    def test_nested_loops(self, parser):
        """Test: ciclos anidados"""
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

        ast = parser.parse(code)
        outer_loop = ast.algorithm.body.statements[0]

        assert isinstance(outer_loop, ForLoopNode)
        assert len(outer_loop.body.statements) == 1

        inner_loop = outer_loop.body.statements[0]
        assert isinstance(inner_loop, ForLoopNode)

class TestParserConditionals:
    """Tests de condicionales"""

    @pytest.fixture
    def parser(self):
        return PseudocodeParser()

    def test_if_statement(self, parser):
        """Test: IF sin ELSE"""
        code = """
        algorithm test(x)
        begin
            if (x > 0) then
            begin
                x ← x + 1
            end
        end
        """

        ast = parser.parse(code)
        statement = ast.algorithm.body.statements[0]

        assert isinstance(statement, IfStatementNode)
        assert statement.else_block is None

    def test_if_else_statement(self, parser):
        """Test: IF con ELSE"""
        code = """
        algorithm test(x)
        begin
            if (x > 0) then
            begin
                x ← x + 1
            end
            else
            begin
                x ← x - 1
            end
        end
        """

        ast = parser.parse(code)
        statement = ast.algorithm.body.statements[0]

        assert isinstance(statement, IfStatementNode)
        assert statement.else_block is not None

class TestParserExpressions:
    """Tests de expresiones"""

    @pytest.fixture
    def parser(self):
        return PseudocodeParser()

    def test_arithmetic_expression(self, parser):
        """Test: expresión aritmética"""
        code = """
        algorithm test()
        begin
            x ← 2 + 3 * 4
        end
        """

        ast = parser.parse(code)
        assignment = ast.algorithm.body.statements[0]

        assert isinstance(assignment, AssignmentNode)
        assert isinstance(assignment.value, BinaryOpNode)

    def test_comparison_expression(self, parser):
        """Test: expresión de comparación"""
        code = """
        algorithm test(n)
        begin
            if (n > 10) then
            begin
                x ← 1
            end
        end
        """

        ast = parser.parse(code)
        if_stmt = ast.algorithm.body.statements[0]

        assert isinstance(if_stmt.condition, BinaryOpNode)
        assert if_stmt.condition.operator == '>'

    def test_logical_expression(self, parser):
        """Test: expresión lógica"""
        code = """
        algorithm test(x, y)
        begin
            if (x > 0 and y < 10) then
            begin
                z ← 1
            end
        end
        """

        ast = parser.parse(code)
        if_stmt = ast.algorithm.body.statements[0]

        assert isinstance(if_stmt.condition, BinaryOpNode)
        assert if_stmt.condition.operator == 'and'

class TestParserArrays:
    """Tests de arrays"""

    @pytest.fixture
    def parser(self):
        return PseudocodeParser()

    def test_array_parameter(self, parser):
        """Test: parámetro array"""
        code = """
        algorithm test(A[10])
        begin
            x ← A[1]
        end
        """

        ast = parser.parse(code)
        param = ast.algorithm.parameters[0]

        assert param.param_type == "array"
        assert param.name == "A"
        assert param.array_dimensions == [10]

    def test_array_access(self, parser):
        """Test: acceso a array"""
        code = """
        algorithm test(A[10])
        begin
            x ← A[5]
        end
        """

        ast = parser.parse(code)
        # El acceso a array está en la expresión de la asignación
        # Verificamos que el AST se construyó correctamente
        assert ast is not None

class TestParserCalls:
    """Tests de llamadas a funciones"""

    @pytest.fixture
    def parser(self):
        return PseudocodeParser()

    def test_call_statement(self, parser):
        """Test: llamada a función"""
        code = """
        algorithm test(n)
        begin
            call helper(n)
        end
        """

        ast = parser.parse(code)
        statement = ast.algorithm.body.statements[0]

        assert isinstance(statement, CallStatementNode)
        assert statement.function_name == "helper"
        assert len(statement.arguments) == 1

class TestParserErrors:
    """Tests de manejo de errores"""

    @pytest.fixture
    def parser(self):
        return PseudocodeParser()

    def test_syntax_error(self, parser):
        """Test: error de sintaxis"""
        code = """
        algorithm test(n
        begin
            x ← 1
        end
        """

        with pytest.raises(SyntaxErrorException):
            parser.parse(code)

    def test_empty_code(self, parser):
        """Test: código vacío"""
        with pytest.raises(ParserException):
            parser.parse("")

    def test_code_too_large(self, parser):
        """Test: código demasiado grande"""
        # Generar código muy grande
        lines = ["x ← x + 1"] * 2000
        code = f"algorithm test()\nbegin\n{chr(10).join(lines)}\nend"

        with pytest.raises(Exception):  # AlgorithmTooLargeException
            parser.parse(code)

class TestParserPSeIntCompatibility:
    """Tests de compatibilidad con sintaxis PSeInt"""

    @pytest.fixture
    def parser(self):
        return PseudocodeParser()

    def test_spanish_keywords(self, parser):
        """Test: palabras clave en español"""
        code = """
        algoritmo prueba(n)
        inicio
            para i ← 1 hasta n hacer
            inicio
                x ← x + 1
            fin
        fin
        """

        ast = parser.parse(code)

        assert ast.algorithm.name == "prueba"
        assert isinstance(ast.algorithm.body.statements[0], ForLoopNode)

    def test_mixed_keywords(self, parser):
        """Test: palabras clave mezcladas"""
        code = """
        algorithm test(n)
        inicio
            if (n > 0) entonces
            begin
                x ← 1
            end
        fin
        """

        # Debe parsear correctamente aunque mezcle inglés y español
        ast = parser.parse(code)
        assert ast is not None

class TestParserRealWorldExamples:
    """Tests con algoritmos reales"""

    @pytest.fixture
    def parser(self):
        return PseudocodeParser()

    def test_bubble_sort(self, parser):
        """Test: Bubble Sort"""
        code = """
        algorithm bubbleSort(A[n])
        begin
            for i ← 1 to n - 1 do
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

        ast = parser.parse(code)

        assert ast.algorithm.name == "bubbleSort"
        assert len(ast.algorithm.parameters) == 1
        assert ast.algorithm.parameters[0].param_type == "array"

    def test_binary_search(self, parser):
        """Test: Binary Search"""
        code = """
        algorithm binarySearch(A[n], x)
        begin
            left ← 1
            right ← n

            while (left <= right) do
            begin
                mid ← (left + right) / 2

                if (A[mid] = x) then
                begin
                    return mid
                end

                if (A[mid] < x) then
                begin
                    left ← mid + 1
                end
                else
                begin
                    right ← mid - 1
                end
            end

            return -1
        end
        """

        ast = parser.parse(code)

        assert ast.algorithm.name == "binarySearch"
        assert len(ast.algorithm.parameters) == 2

    def test_fibonacci_recursive(self, parser):
        """Test: Fibonacci recursivo"""
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

        ast = parser.parse(code)

        assert ast.algorithm.name == "fibonacci"

# Fixtures y Helpers

@pytest.fixture
def sample_algorithms():
    """Fixture con algoritmos de ejemplo"""
    return {
        "simple": """
            algorithm simple()
            begin
                x ← 1
            end
        """,
        "with_params": """
            algorithm test(a, b, c)
            begin
                result ← a + b + c
            end
        """,
        "with_array": """
            algorithm arrayTest(A[10])
            begin
                sum ← 0
                for i ← 1 to 10 do
                begin
                    sum ← sum + A[i]
                end
            end
        """
    }

@pytest.mark.parametrize("algorithm_name", ["simple", "with_params", "with_array"])
def test_sample_algorithms(algorithm_name, sample_algorithms):
    """Test parametrizado con múltiples algoritmos"""
    parser = PseudocodeParser()
    code = sample_algorithms[algorithm_name]

    ast = parser.parse(code)
    assert ast is not None
    assert ast.algorithm is not None