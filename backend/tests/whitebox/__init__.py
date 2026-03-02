"""
Módulo de White Box Tests para el backend de Complexity Analyzer.

Pruebas de caja blanca que recorren ramas internas del código fuente,
verificando caminos de ejecución, condiciones límite y cobertura de
decisión en cada componente.

- test_whitebox.py: Cobertura de ramas internas de todos los módulos core.
    - TestParserInternalBranches: Ramas del parser (éxito, error, validación).
    - TestASTBuilderBranches: Construcción de nodos AST (LValue, ForLoop, While,
      If/Else, BinaryOp, Literal, FunctionCall, Return, RepeatUntil, parámetros).
    - TestSemanticAnalyzerBranches: Análisis semántico (variables no declaradas,
      recursión, funciones builtin, tabla de símbolos).
    - TestASTValidatorBranches: Validación de AST (cuerpos vacíos, anidamiento
      profundo, estadísticas y conversión booleana).
    - TestAnalyzerEngineBranches: Motor de análisis (opciones habilitadas/deshabilitadas,
      línea por línea, espacial, recursivo, resumen, to_dict).
    - TestExecutionCounterBranches: Conteo de ejecuciones (constante, lineal,
      cuadrático, if-statement, while-loop, anidamiento).
    - TestPatternDetectorBranches: Detección de patrones (brute_force, divide_and_conquer,
      dynamic_programming, greedy, backtracking, sin patrones).
    - TestPatternScorerBranches: Puntuación de patrones (nombre de nivel de confianza,
      score alto/bajo/medio, ordenamiento por score).
    - TestPatternMatcherBranches: Coincidencia de patrones (loops anidados, llamadas
      recursivas, recursión condicional, array/tabla, sin coincidencia).
    - TestStructureIdentifierBranches: Identificación de estructuras (array, stack,
      dictionary, sin estructuras, tipo específico, múltiples estructuras).
    - TestASTNodesCoverage: Cobertura de nodos AST (repr, to_dict, ClassDefinition,
      ForLoop, IfStatement, expresiones).

Para ejecutar los whitebox tests:
	pytest tests/whitebox/ -m whitebox
"""
