"""
Módulo de Black Box Tests para el backend de Complexity Analyzer.

Pruebas de caja negra basadas en técnicas clásicas: partición de equivalencia,
valores frontera, tablas de decisión y error guessing. Se evalúa el
comportamiento externo del sistema sin conocimiento de la implementación.

- test_blackbox.py: Pruebas de caja negra para la API.
    - TestAnalysisEquivalencePartitions: Particiones de equivalencia para análisis
      (constante, lineal, cuadrático, recursivo, divide & conquer, cuerpo vacío,
      sintaxis inválida).
    - TestBoundaryValues: Valores frontera (algoritmo mínimo, sentencia única,
      muchos parámetros, confianza cero/máxima, código vacío, solo espacios).
    - TestDecisionTable: Tablas de decisión (combinaciones de opciones de análisis,
      niveles de validación, formatos de exportación).
    - TestErrorGuessing: Error guessing (unicode, nombres largos, if/else profundamente
      anidado, múltiples return, body faltante, null, acceso a arrays, while loop).
    - TestPatternBlackBox: Detección de patrones como caja negra.
    - TestStructureBlackBox: Detección de estructuras como caja negra.

Para ejecutar los blackbox tests:
	pytest tests/blackbox/ -m blackbox
"""
