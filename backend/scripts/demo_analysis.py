"""
Script de Demostración - Análisis de Complejidad

Script para probar el analizador de complejidad con diferentes algoritmos.
Ejecutar: python scripts/demo_analysis.py
"""

import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.analyzer.analyzer_engine import AnalyzerEngine
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def analyze_algorithm(name: str, code: str):
    """
    Analiza un algoritmo y muestra resultados.
    
    Args:
        name: Nombre del algoritmo
        code: Código pseudocódigo
    """
    print(f"ANALIZANDO: {name}")

    print("CÓDIGO:")
    print(code)
    print()
    
    try:
        # Crear motor de análisis
        engine = AnalyzerEngine()
        
        # Analizar
        result = engine.analyze_from_code(
            pseudocode=code,
            include_line_by_line=True
        )
        
        # Mostrar resultados
        print("RESULTADOS:")
        print(f"Algoritmo: {result.algorithm_name}")
        print(f"Big O (peor caso): {result.big_o}")
        print(f"Omega (mejor caso): {result.omega}")
        
        if result.theta:
            print(f"Theta (caso promedio): {result.theta}")
        else:
            print("Theta: No existe (Big O ≠ Omega)")
        
        # Metadata
        if result.metadata:
            print(f"\nClase de complejidad: {result.metadata.get('complexity_class', 'N/A')}")
            print(f"Cota ajustada: {'Sí' if result.metadata.get('tight_bound') else 'No'}")
            
            warnings = result.metadata.get('warnings', [])
            if warnings:
                print("\nADVERTENCIAS:")
                for warning in warnings:
                    print(f"{warning}")
        
        # Análisis línea por línea
        if result.line_by_line:
            print("\nANÁLISIS LÍNEA POR LÍNEA:")
            
            stats = result.line_by_line.get('statistics', {})
            print(f"Total de líneas: {stats.get('total_lines', 0)}")
            
            most_executed = stats.get('most_executed')
            if most_executed:
                print(f"Línea más ejecutada: Línea {most_executed['line_number']}")
                print(f"  Código: {most_executed['code']}")
                print(f"  Ejecuciones: {most_executed['executions']}")
        
        # Resumen
        print("\nRESUMEN:")
        print(engine.get_complexity_summary(result))
        
    except Exception as e:
        print(f"\nERROR: {e}")
        logger.exception(f"Error analizando {name}")


def main():
    """Función principal"""
    print("DEMOSTRACIÓN - ANALIZADOR DE COMPLEJIDAD")
    
    # Algoritmo 1: Constante O(1)
    analyze_algorithm(
        "Algoritmo Constante",
        """
        algorithm constant(n)
        begin
            x ← 1
            y ← 2
            z ← x + y
        end
        """
    )
    
    # Algoritmo 2: Lineal O(n)
    analyze_algorithm(
        "Linear Search",
        """
        algorithm linearSearch(A[1..n], x)
        begin
            for i ← 1 to n do
                if A[i] = x then
                    return i
            return -1
        end
        """
    )
    
    # Algoritmo 3: Cuadrático O(n²)
    analyze_algorithm(
        "Bubble Sort",
        """
        algorithm bubbleSort(A[1..n])
        begin
            for i ← 1 to n-1 do
                for j ← 1 to n-i do
                    if A[j] > A[j+1] then
                    begin
                        temp ← A[j]
                        A[j] ← A[j+1]
                        A[j+1] ← temp
                    end
        end
        """
    )
    
    # Algoritmo 4: Loops secuenciales
    analyze_algorithm(
        "Loops Secuenciales",
        """
        algorithm sequential(A[1..n], B[1..n])
        begin
            for i ← 1 to n do
                sum ← sum + A[i]
            
            for j ← 1 to n do
                prod ← prod * B[j]
        end
        """
    )
    
    # Algoritmo 5: IF con diferentes complejidades
    analyze_algorithm(
        "Conditional Complexity",
        """
        algorithm conditional(A[1..n], mode)
        begin
            if mode = "slow" then
            begin
                for i ← 1 to n do
                    for j ← 1 to n do
                        x ← A[i] + A[j]
            end
            else
                x ← A[1]
        end
        """
    )
    print("DEMOSTRACIÓN COMPLETADA")

if __name__ == "__main__":
    main()