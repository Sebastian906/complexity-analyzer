"""
Módulo de Regression Tests para el backend de Complexity Analyzer.

Fija resultados conocidos como correctos para 10 algoritmos canónicos.
Si alguna refactorización o cambio futuro modifica el comportamiento del
analizador, estos tests fallarán para alertar de la regresión.

- test_regression.py: Pruebas de regresión sobre algoritmos canónicos.
    - TestComplexityRegression: Big-O reportado por la API se mantiene estable
      para cada algoritmo canónico.
    - TestRecursionRegression: Detección de recursión vía API (is_recursive)
      se mantiene correcta.
    - TestDirectAnalysisRegression: Big-O y flag de recursión del AnalyzerEngine
      directo se mantienen estables.
    - TestPatternRegression: Patrones detectados (brute_force, recursive,
      divide_and_conquer, etc.) se mantienen para cada algoritmo.
    - TestStructureRegression: Estructuras detectadas (array en sum_array,
      bubble_sort; ausencia en constant) se mantienen.
    - TestParserRegression: El parser produce ASTs estables (parse exitoso,
      to_dict serializable, nombre y parámetros preservados).
    - TestValidationRegression: Validación vía API acepta algoritmos válidos
      y rechaza código inválido.
    - TestQuickAnalysisRegression: Análisis rápido vía endpoint quick se
      mantiene estable.

Para ejecutar los regression tests:
	pytest tests/regression/ -m regression
"""
