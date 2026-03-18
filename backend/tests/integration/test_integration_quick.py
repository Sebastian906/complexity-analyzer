"""
Test Rápido de Integración

Verifica que el parser y los analizadores funcionen juntos correctamente.
Ejecutar: python scripts/test_integration_quick.py
"""

import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.parser.pseudocode_parser import PseudocodeParser
from app.core.analyzer.complexity.big_o_analyzer import BigOAnalyzer
from app.core.analyzer.complexity.omega_analyzer import OmegaAnalyzer
from app.core.analyzer.complexity.theta_analyzer import ThetaAnalyzer
from app.core.analyzer.complexity.complexity_calculator import ComplexityCalculator
from app.core.analyzer.line_by_line_analyzer import LineByLineAnalyzer
from app.core.analyzer.analyzer_engine import AnalyzerEngine


def test_simple_algorithm():
    """Test con algoritmo simple"""
    print("TEST 1: Algoritmo Simple - O(n)")
    
    code = """
    algorithm test(n)
    begin
        for i ← 1 to n do
            x ← i
    end
    """
    
    try:
        # Parsear
        parser = PseudocodeParser()
        ast = parser.parse(code)
        print(f"✓ Parsing exitoso: {ast.algorithm.name}")
        
        # Analizar con Big O
        big_o_analyzer = BigOAnalyzer()
        result = big_o_analyzer.analyze(ast)
        print(f"✓ Big O: {result['complexity']}")
        
        # Analizar con Omega
        omega_analyzer = OmegaAnalyzer()
        result = omega_analyzer.analyze(ast)
        print(f"✓ Omega: {result['complexity']}")
        
        # Analizar con Theta
        theta_analyzer = ThetaAnalyzer()
        result = theta_analyzer.analyze(ast, big_o="O(n)", omega="Ω(n)")
        print(f"✓ Theta: {result['complexity']}")
        
        print("Test 1 PASSED\n")
        return True
        
    except Exception as e:
        print(f"Test 1 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_nested_loops():
    """Test con loops anidados"""
    print("TEST 2: Loops Anidados - O(n²)")
    
    code = """
    algorithm bubbleSort(A[1..n])
    begin
        for i ← 1 to n do
            for j ← 1 to n do
                if A[j] > A[j+1] then
                    temp ← A[j]
    end
    """
    
    try:
        parser = PseudocodeParser()
        ast = parser.parse(code)
        print(f"✓ Parsing exitoso: {ast.algorithm.name}")
        
        # Usar el calculador completo
        calculator = ComplexityCalculator()
        result = calculator.calculate(ast)
        
        print(f"✓ Big O: {result.big_o}")
        print(f"✓ Omega: {result.omega}")
        print(f"✓ Theta: {result.theta if result.theta else 'No existe'}")
        print(f"✓ Cota ajustada: {'Sí' if result.tight_bound else 'No'}")
        
        print("Test 2 PASSED\n")
        return True
        
    except Exception as e:
        print(f"Test 2 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_line_by_line():
    """Test de análisis línea por línea"""
    print("TEST 3: Análisis Línea por Línea")

    code = """
    algorithm test(n)
    begin
        x ← 1
        for i ← 1 to n do
            y ← i
    end
    """
    
    try:
        parser = PseudocodeParser()
        ast = parser.parse(code)
        print(f"✓ Parsing exitoso: {ast.algorithm.name}")
        
        # Análisis línea por línea
        line_analyzer = LineByLineAnalyzer()
        result = line_analyzer.analyze(ast, code)
        
        print(f"✓ Total de líneas analizadas: {result['statistics']['total_lines']}")
        
        for line in result['lines'][:5]:  # Mostrar primeras 5 líneas
            print(f"  Línea {line['line_number']}: {line['executions']} ejecuciones")
        
        print("Test 3 PASSED\n")
        return True
        
    except Exception as e:
        print(f"Test 3 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_full_engine():
    """Test del motor completo"""
    print("TEST 4: Motor de Análisis Completo")

    code = """
    algorithm quicksort(A[1..n])
    begin
        if n > 1 then
        begin
            for i ← 1 to n do
                x ← A[i]
        end
    end
    """
    
    try:
        engine = AnalyzerEngine()
        result = engine.analyze_from_code(code, include_line_by_line=True)
        
        print(f"✓ Algoritmo: {result.algorithm_name}")
        print(f"✓ Big O: {result.big_o}")
        print(f"✓ Omega: {result.omega}")
        print(f"✓ Theta: {result.theta if result.theta else 'No existe'}")
        
        if result.metadata:
            if isinstance(result.metadata, dict):
                complexity_class = result.metadata.get('complexity_class', 'N/A')
                warnings = result.metadata.get('warnings', [])
            else:
                complexity_class = getattr(result.metadata, 'complexity_class', 'N/A')
                warnings = getattr(result.metadata, 'warnings', [])

            print(f"✓ Clase: {complexity_class}")
            if warnings:
                print(f"  Advertencias: {len(warnings)}")
        
        print("Test 4 PASSED\n")
        return True
        
    except Exception as e:
        print(f"Test 4 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar todos los tests"""
    print("TESTS DE INTEGRACIÓN - PARSER + ANALIZADORES")
    
    results = []
    
    # Ejecutar tests
    results.append(("Algoritmo Simple", test_simple_algorithm()))
    results.append(("Loops Anidados", test_nested_loops()))
    results.append(("Línea por Línea", test_line_by_line()))
    results.append(("Motor Completo", test_full_engine()))
    
    # Resumen
    print("RESUMEN")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n ¡TODOS LOS TESTS PASARON!")
        return 0
    else:
        print(f"\n {total - passed} test(s) fallaron")
        return 1


if __name__ == "__main__":
    sys.exit(main())