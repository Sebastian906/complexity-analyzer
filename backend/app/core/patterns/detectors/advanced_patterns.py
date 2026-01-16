"""
Advanced Pattern Detectors
Detectores para patrones avanzados y especializados
"""

from typing import Dict, Any
from app.core.parser.ast_nodes import ASTNode, AlgorithmNode, ForLoopNode
from app.core.patterns.base_pattern import (
    BasePatternDetector, PatternType, PatternIndicator, PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher

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
    """
    Detector de algoritmos bio-inspirados 
    
    CRITERIOS MUY ESTRICTOS:
    1. Debe tener variables de población (population, individuals, generation)
    2. Debe tener operadores evolutivos (crossover, mutation, selection)
    3. Debe tener función de fitness
    4. NO es bio-inspirado solo por tener loops anidados
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.BIO_INSPIRED
        self.pattern_name = "Algoritmo Bio-inspirado"
        self.description = "Algoritmo inspirado en procesos biológicos"
        self.typical_complexity = "Variable"

        self._indicators = [
            PatternIndicator("population_variables", "Variables de población", False, 5.0),
            PatternIndicator("evolutionary_ops", "Operadores evolutivos", False, 5.0),
            PatternIndicator("fitness_function", "Función de fitness", False, 4.0),
            PatternIndicator("selection_mechanism", "Mecanismo de selección", False, 3.0)
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta algoritmos bio-inspirados con CRITERIOS ESTRICTOS"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. Variables de población (CRÍTICO)
        pop_vars = self._indicators[0]
        if analysis.get("has_population_vars"):
            pop_vars.found = True
            pop_vars.evidence = f"Variables detectadas: {', '.join(analysis['population_vars'])}"
            indicators_found.append(pop_vars)
        else:
            indicators_missing.append(pop_vars)

        # 2. Operadores evolutivos (CRÍTICO)
        evo_ops = self._indicators[1]
        if analysis.get("has_evolutionary_ops"):
            evo_ops.found = True
            evo_ops.evidence = f"Operadores: {', '.join(analysis['evolutionary_ops'])}"
            indicators_found.append(evo_ops)
        else:
            indicators_missing.append(evo_ops)

        # 3. Función de fitness (IMPORTANTE)
        fitness = self._indicators[2]
        if analysis.get("has_fitness"):
            fitness.found = True
            fitness.evidence = "Función de evaluación detectada"
            indicators_found.append(fitness)
        else:
            indicators_missing.append(fitness)

        # 4. Mecanismo de selección
        selection = self._indicators[3]
        if analysis.get("has_selection"):
            selection.found = True
            selection.evidence = "Mecanismo de selección detectado"
            indicators_found.append(selection)
        else:
            indicators_missing.append(selection)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)

        # REGLA ESTRICTA: Si NO tiene variables de población Y operadores evolutivos, NO es bio-inspirado
        if not (analysis.get("has_population_vars") and analysis.get("has_evolutionary_ops")):
            confidence = min(confidence * 0.05, 0.10)  # Máximo 10%
            reasoning = (
                "NO es algoritmo bio-inspirado: falta terminología específica de "
                "evolución (population, crossover, mutation, fitness, generation). "
                "Los algoritmos bio-inspirados requieren estos componentes explícitos."
            )
        else:
            reasoning = (
                f"Algoritmo bio-inspirado detectado con {len(indicators_found)} "
                f"indicadores característicos de algoritmos evolutivos/genéticos."
            )

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Análisis ESTRICTO de bio-inspirado"""
        from app.core.parser.ast_nodes import VariableNode, AssignmentNode, CallStatementNode
        
        analysis = {
            "has_population_vars": False,
            "has_evolutionary_ops": False,
            "has_fitness": False,
            "has_selection": False,
            "population_vars": [],
            "evolutionary_ops": [],
        }

        # Palabras clave ESPECÍFICAS de bio-inspirados
        population_keywords = {
            'population', 'individuals', 'generation', 'chromosome', 
            'genome', 'species', 'offspring', 'parents'
        }
        
        evolutionary_keywords = {
            'crossover', 'mutation', 'mutate', 'breed', 'evolve',
            'recombination', 'genetic', 'evolutionary'
        }
        
        fitness_keywords = {
            'fitness', 'evaluate', 'adaptation', 'survival'
        }
        
        selection_keywords = {
            'select', 'tournament', 'roulette', 'elitism', 'selection'
        }

        # Colectar todas las variables y nombres de funciones
        all_names = set()
        
        def _collect_names(node: ASTNode):
            if isinstance(node, VariableNode):
                all_names.add(node.name.lower())
            elif isinstance(node, AssignmentNode):
                if hasattr(node.target, 'name'):
                    all_names.add(node.target.name.lower())
            elif isinstance(node, CallStatementNode):
                all_names.add(node.function_name.lower())
            
            from app.core.patterns.pattern_matcher import get_node_children
            for child in get_node_children(node):
                _collect_names(child)
        
        _collect_names(ast)
        
        # Buscar palabras clave
        for name in all_names:
            # Variables de población
            if any(kw in name for kw in population_keywords):
                analysis["population_vars"].append(name)
            
            # Operadores evolutivos
            if any(kw in name for kw in evolutionary_keywords):
                analysis["evolutionary_ops"].append(name)
            
            # Fitness
            if any(kw in name for kw in fitness_keywords):
                analysis["has_fitness"] = True
            
            # Selección
            if any(kw in name for kw in selection_keywords):
                analysis["has_selection"] = True
        
        analysis["has_population_vars"] = len(analysis["population_vars"]) > 0
        analysis["has_evolutionary_ops"] = len(analysis["evolutionary_ops"]) > 0

        return analysis

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

        for ind in self._indicators:
            if analysis.get("has_greedy_structure"):
                ind.found = True
                indicators_found.append(ind)
            else:
                indicators_missing.append(ind)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)
        
        # Penalización por defecto - muy difícil de detectar
        confidence = min(confidence * 0.3, 0.3)
        
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
        result = PatternMatcher.has_greedy_choice(ast)
        return {
            "has_greedy_structure": result.matched
        }