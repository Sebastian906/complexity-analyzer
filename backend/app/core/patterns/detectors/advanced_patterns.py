"""
Advanced Pattern Detectors
Detectores para patrones avanzados y especializados
"""

from typing import Dict, Any
from app.core.parser.ast_nodes import ASTNode, AlgorithmNode
from app.core.patterns.base_pattern import (
    BasePatternDetector, PatternType, PatternIndicator, PatternMatch
)

class QuantumAlgorithmsDetector(BasePatternDetector):
    """Detector de algoritmos cuánticos (muy especializado)"""

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.QUANTUM
        self.pattern_name = "Algoritmo Cuántico"
        self.description = "Algoritmo cuántico (requiere análisis especializado)"
        self.typical_complexity = "Variable"

        self._indicators = [
            PatternIndicator("quantum_gates", "Uso de puertas cuánticas", False, 4.0),
            PatternIndicator("superposition", "Superposición", False, 3.5),
            PatternIndicator("entanglement", "Entrelazamiento", False, 3.0)
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta algoritmos cuánticos"""
        # Los algoritmos cuánticos son difíciles de detectar en pseudocódigo estándar
        # Se recomienda usar LLM para este análisis

        indicators_found = []
        indicators_missing = self._indicators

        reasoning = (
            "Los algoritmos cuánticos requieren análisis especializado "
            "y típicamente se expresan con notación cuántica específica. "
            "Se recomienda validación con LLM."
        )

        return self._create_match(
            confidence=0.0,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Análisis no aplicable para pseudocódigo estándar"""
        return {}

class BioInspiredDetector(BasePatternDetector):
    """Detector de algoritmos bio-inspirados"""

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.BIO_INSPIRED
        self.pattern_name = "Algoritmo Bio-inspirado"
        self.description = "Algoritmo inspirado en procesos biológicos"
        self.typical_complexity = "Variable"

        self._indicators = [
            PatternIndicator("population_based", "Basado en población", False, 4.0),
            PatternIndicator("evolutionary_ops", "Operaciones evolutivas", False, 3.5),
            PatternIndicator("fitness_function", "Función de fitness", False, 3.0),
            PatternIndicator("selection_mechanism", "Mecanismo de selección", False, 2.5)
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta algoritmos bio-inspirados"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # Buscar características básicas
        for ind in self._indicators:
            if analysis.get("has_population_loop"):
                ind.found = True
                indicators_found.append(ind)
            else:
                indicators_missing.append(ind)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)
        reasoning = (
            "Algoritmos bio-inspirados típicamente manejan poblaciones "
            "y operadores evolutivos. Análisis limitado en pseudocódigo."
        )

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Análisis básico"""
        from app.core.parser.ast_nodes import ForLoopNode
        from app.core.patterns.pattern_matcher import PatternMatcher

        # Bio-inspirados típicamente tienen loops sobre poblaciones
        loops = PatternMatcher._count_nodes_of_type(ast, (ForLoopNode,))

        return {
            "has_population_loop": loops >= 2
        }

class ApproximationDetector(BasePatternDetector):
    """Detector de algoritmos de aproximación"""

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.APPROXIMATION
        self.pattern_name = "Algoritmo de Aproximación"
        self.description = "Algoritmo que aproxima solución óptima"
        self.typical_complexity = "Variable (polinomial típicamente)"

        self._indicators = [
            PatternIndicator("relaxation", "Relajación del problema", False, 4.0),
            PatternIndicator("heuristic_choice", "Elección heurística", False, 3.5),
            PatternIndicator("approximation_factor", "Factor de aproximación", False, 3.0),
            PatternIndicator("polynomial_time", "Tiempo polinomial", False, 2.5)
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta algoritmos de aproximación"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # Aproximación es similar a Greedy pero para problemas NP-hard
        # Difícil de detectar sin contexto del problema

        for ind in self._indicators:
            if analysis.get("has_greedy_structure"):
                ind.found = True
                indicators_found.append(ind)
            else:
                indicators_missing.append(ind)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)
        reasoning = (
            "Algoritmos de aproximación son difíciles de distinguir "
            "de algoritmos greedy sin conocer el contexto del problema. "
            "Se recomienda validación con LLM."
        )

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Análisis básico"""
        from app.core.patterns.pattern_matcher import PatternMatcher

        # Aproximación típicamente usa heurísticas (similar a greedy)
        result = PatternMatcher.has_greedy_choice(ast)

        return {
            "has_greedy_structure": result.matched
        }