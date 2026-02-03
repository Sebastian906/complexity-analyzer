"""
Tests para el Lexer del Parser de Pseudocódigo

Verifica que la tokenización funcione correctamente para todos
los tokens definidos en la gramática.
"""

import pytest
from lark import Lark, Token
from lark.exceptions import UnexpectedCharacters, UnexpectedToken

from app.core.parser.grammar import GRAMMAR_FILE

@pytest.fixture
def parser():
    """Crea una instancia del parser Lark"""
    with open(GRAMMAR_FILE, 'r', encoding='utf-8') as f:
        grammar = f.read()
    
    return Lark(
        grammar,
        start='start',
        parser='lalr',
        propagate_positions=True,
    )

class TestKeywordsTokenization:
    """Tests para tokenización de palabras clave"""
    
    def test_algorithm_keywords(self, parser):
        """Verifica que las palabras clave de algoritmo se reconozcan"""
        code = "algorithm test(n) begin end"
        tree = parser.parse(code)
        assert tree is not None
    
    def test_spanish_keywords(self, parser):
        """Verifica palabras clave en español"""
        code = "algoritmo test(n) inicio fin"
        tree = parser.parse(code)
        assert tree is not None
    
    def test_loop_keywords(self, parser):
        """Verifica palabras clave de ciclos"""
        keywords = [
            ("for i ← 1 to n do begin end", "for"),
            ("para i ← 1 hasta n hacer inicio fin", "para"),
            ("while (i < n) do begin end", "while"),
            ("mientras (i < n) hacer inicio fin", "mientras"),
            ("repeat x ← x + 1 until (i > 0)", "repeat"),
        ]
        
        for code, keyword in keywords:
            full_code = f"algorithm test(n) begin {code} end"
            tree = parser.parse(full_code)
            assert tree is not None, f"Failed to parse {keyword}"
    
    def test_conditional_keywords(self, parser):
        """Verifica palabras clave condicionales"""
        code = "algorithm test(n) begin if (n > 0) then begin x ← 1 end else begin x ← 0 end end"
        tree = parser.parse(code)
        assert tree is not None
    
    def test_logical_operators(self, parser):
        """Verifica operadores lógicos"""
        # Operadores binarios (and, or)
        binary_operators = ["and", "&&", "or", "||"]
        
        for op in binary_operators:
            code = f"algorithm test(n) begin if (n > 0 {op} n < 10) then begin x ← 1 end end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with binary operator: {op}"
        
        # Operadores unarios (not) - sintaxis diferente
        unary_operators = ["not", "no", "!"]
        
        for op in unary_operators:
            code = f"algorithm test(n) begin if ({op} n > 0) then begin x ← 1 end end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with unary operator: {op}"

class TestLiteralsTokenization:
    """Tests para tokenización de literales"""
    
    def test_integer_numbers(self, parser):
        """Verifica números enteros"""
        numbers = ["0", "1", "42", "999", "123456"]
        
        for num in numbers:
            code = f"algorithm test(n) begin x ← {num} end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with number: {num}"
    
    def test_float_numbers(self, parser):
        """Verifica números decimales"""
        numbers = ["0.0", "1.5", "3.14159", "99.99"]
        
        for num in numbers:
            code = f"algorithm test(n) begin x ← {num} end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with number: {num}"
    
    def test_scientific_notation(self, parser):
        """Verifica notación científica"""
        # La gramática actual solo soporta notación científica con enteros: \d+e[+-]?\d+
        # Ejemplos válidos: 1e10, 2e-3, 1E10, 3e+2
        numbers = ["1e10", "2e3", "1E10", "3e2", "5e-2", "7e+3"]
        
        for num in numbers:
            code = f"algorithm test(n) begin x ← {num} end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with number: {num}"
    
    def test_boolean_literals(self, parser):
        """Verifica literales booleanos"""
        booleans = [
            "TRUE", "true", "True",
            "FALSE", "false", "False",
            "VERDADERO", "verdadero",
            "FALSO", "falso"
        ]
        
        for bool_val in booleans:
            code = f"algorithm test(n) begin x ← {bool_val} end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with boolean: {bool_val}"
    
    def test_string_literals_double_quotes(self, parser):
        """Verifica strings con comillas dobles"""
        strings = [
            '""',
            '"hello"',
            '"Hello World"',
            '"123"',
            '"test with spaces"'
        ]
        
        for string in strings:
            code = f"algorithm test(n) begin x ← {string} end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with string: {string}"
    
    def test_string_literals_single_quotes(self, parser):
        """Verifica strings con comillas simples"""
        strings = [
            "''",
            "'hello'",
            "'Hello World'",
            "'123'"
        ]
        
        for string in strings:
            code = f"algorithm test(n) begin x ← {string} end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with string: {string}"

class TestIdentifiersTokenization:
    """Tests para tokenización de identificadores"""
    
    def test_simple_identifiers(self, parser):
        """Verifica identificadores simples"""
        identifiers = [
            "x", "y", "z",
            "variable", "count", "sum",
            "i", "j", "k",
            "myVar", "myVariable123"
        ]
        
        for ident in identifiers:
            code = f"algorithm test(n) begin {ident} ← 1 end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with identifier: {ident}"
    
    def test_identifiers_with_underscores(self, parser):
        """Verifica identificadores con guiones bajos"""
        identifiers = [
            "_x", "x_", "_x_",
            "my_var", "my_long_variable_name",
            "_private", "PUBLIC_"
        ]
        
        for ident in identifiers:
            code = f"algorithm test(n) begin {ident} ← 1 end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with identifier: {ident}"
    
    def test_identifiers_with_accents(self, parser):
        """Verifica identificadores con acentos (español)"""
        identifiers = [
            "número", "índice", "año",
            "ección", "información"
        ]
        
        for ident in identifiers:
            code = f"algorithm test(n) begin {ident} ← 1 end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with identifier: {ident}"
    
    def test_class_names(self, parser):
        """Verifica nombres de clases (PascalCase)"""
        class_names = [
            "Node", "Tree", "Graph",
            "MyClass", "DataStructure"
        ]
        
        for class_name in class_names:
            # Probar definición de clase con atributos y uso en algoritmo
            code = f"{class_name} {{ x y }} algorithm test(n) begin end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with class name: {class_name}"

class TestOperatorsTokenization:
    """Tests para tokenización de operadores"""
    
    def test_arithmetic_operators(self, parser):
        """Verifica operadores aritméticos"""
        operators = ["+", "-", "*", "/", "^", "%", "div"]
        
        for op in operators:
            code = f"algorithm test(n) begin x ← 5 {op} 3 end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with operator: {op}"
    
    def test_comparison_operators(self, parser):
        """Verifica operadores de comparación"""
        operators = [
            ("<", "menor"),
            (">", "mayor"),
            ("<=", "menor_igual"),
            (">=", "mayor_igual"),
            ("=", "igual"),
            ("!=", "diferente"),
            ("≤", "menor_igual_unicode"),
            ("≥", "mayor_igual_unicode"),
            ("≠", "diferente_unicode")
        ]
        
        for op, name in operators:
            code = f"algorithm test(n) begin if (n {op} 5) then begin x ← 1 end end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with operator: {name}"
    
    def test_assignment_operators(self, parser):
        """Verifica operadores de asignación"""
        operators = ["←", ":="]
        
        for op in operators:
            code = f"algorithm test(n) begin x {op} 5 end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with assignment: {op}"

class TestSpecialSymbolsTokenization:
    """Tests para símbolos especiales"""
    
    def test_mathematical_functions(self, parser):
        """Verifica funciones matemáticas especiales"""
        functions = [
            ("ceil", "ceil(x)"),
            ("floor", "floor(x)"),
            ("length", "length(A)")
        ]
        
        for func_name, func_call in functions:
            code = f"algorithm test(n) begin x ← {func_call} end"
            tree = parser.parse(code)
            assert tree is not None, f"Failed with function: {func_name}"
    
    def test_unicode_mathematical_symbols(self, parser):
        """Verifica símbolos matemáticos Unicode"""
        # La gramática usa sintaxis de función: CEIL "(" expression ")"
        # Los símbolos ⌈ y ⌊ son el inicio del token, requieren paréntesis
        code = "algorithm test(n) begin x ← ceil(5.5) y ← floor(3.7) end"
        tree = parser.parse(code)
        assert tree is not None
    
    def test_unicode_ceil_floor_symbols(self, parser):
        """Verifica símbolos Unicode ⌈ y ⌊ con sintaxis de función"""
        code = "algorithm test(n) begin x ← ⌈(5.5) y ← ⌊(3.7) end"
        tree = parser.parse(code)
        assert tree is not None

class TestCommentsTokenization:
    """Tests para tokenización de comentarios"""
    
    def test_arrow_comments(self, parser):
        """Verifica comentarios con flecha (►)"""
        code = """
        algorithm test(n)
        begin
            ► Este es un comentario
            x ← 1
        end
        """
        tree = parser.parse(code)
        assert tree is not None
    
    def test_double_slash_comments(self, parser):
        """Verifica comentarios con //"""
        code = """
        algorithm test(n)
        begin
            // Este es un comentario
            x ← 1
        end
        """
        tree = parser.parse(code)
        assert tree is not None
    
    def test_inline_comments(self, parser):
        """Verifica comentarios en línea"""
        code = """
        algorithm test(n)
        begin
            x ← 1  ► comentario al final de línea
            y ← 2  // otro comentario
        end
        """
        tree = parser.parse(code)
        assert tree is not None

class TestArrayNotationTokenization:
    """Tests para notación de arrays"""
    
    def test_simple_array_access(self, parser):
        """Verifica acceso simple a arrays"""
        code = "algorithm test(A[1..n]) begin x ← A[1] end"
        tree = parser.parse(code)
        assert tree is not None
    
    def test_multidimensional_arrays(self, parser):
        """Verifica arrays multidimensionales"""
        code = "algorithm test(M[1..n][1..m]) begin x ← M[1][1] end"
        tree = parser.parse(code)
        assert tree is not None
    
    def test_range_notation(self, parser):
        """Verifica notación de rangos"""
        code = "algorithm test(A[1..n]) begin end"
        tree = parser.parse(code)
        assert tree is not None

class TestErrorHandling:
    """Tests para manejo de errores de tokenización"""
    
    def test_invalid_character(self, parser):
        """Verifica que caracteres inválidos lancen error"""
        invalid_codes = [
            "algorithm test(n) begin @ end",  # @ no es válido
            "algorithm test(n) begin $ end",  # $ no es válido
        ]
        
        for code in invalid_codes:
            with pytest.raises(UnexpectedCharacters):
                parser.parse(code)
    
    def test_unclosed_string(self, parser):
        """Verifica error en strings sin cerrar"""
        # Nota: Lark puede manejar esto de diferentes maneras
        code = 'algorithm test(n) begin x ← "unclosed end'
        with pytest.raises((UnexpectedCharacters, UnexpectedToken)):
            parser.parse(code)
    
    def test_invalid_number_format(self, parser):
        """Verifica formato de números inválido"""
        # Números con múltiples puntos decimales
        code = "algorithm test(n) begin x ← 1.2.3 end"
        with pytest.raises(UnexpectedToken):
            parser.parse(code)

class TestWhitespaceHandling:
    """Tests para manejo de espacios en blanco"""
    
    def test_multiple_spaces(self, parser):
        """Verifica que múltiples espacios se ignoren"""
        code = "algorithm    test(n)    begin    x  ←  1    end"
        tree = parser.parse(code)
        assert tree is not None
    
    def test_tabs(self, parser):
        """Verifica que tabs se ignoren"""
        code = "algorithm\ttest(n)\tbegin\tx\t←\t1\tend"
        tree = parser.parse(code)
        assert tree is not None
    
    def test_newlines(self, parser):
        """Verifica que saltos de línea se ignoren"""
        code = """
        algorithm test(n)
        begin
            x ← 1
        end
        """
        tree = parser.parse(code)
        assert tree is not None
    
    def test_mixed_whitespace(self, parser):
        """Verifica combinación de espacios, tabs y newlines"""
        code = """
        algorithm  test(n)
        begin
        	x ← 1
            y ← 2
        end
        """
        tree = parser.parse(code)
        assert tree is not None

# Test Runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])