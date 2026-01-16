"""
Branch and Bound Detector - Detecta algoritmos Branch and Bound

Similar a backtracking pero con poda basada en cotas (bounds).
"""

from typing import Dict, Any
from app.core.parser.ast_nodes import (
    ASTNode, AlgorithmNode, VariableNode, 
    AssignmentNode, BinaryOpNode, IfStatementNode
)
from app.core.patterns.base_pattern import (
    BasePatternDetector, PatternType, PatternIndicator, PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_algorithm_name, get_node_children

class BranchBoundDetector(BasePatternDetector):
    """
    Detector de Branch and Bound - MUY RESTRICTIVO.
    
    Branch and Bound es una técnica AVANZADA que:
    1. Explora árbol de soluciones (como backtracking)
    2. USA COTAS (bounds) para podar ramas
    3. Mantiene MEJOR SOLUCIÓN ACTUAL (best_so_far)
    4. Compara soluciones parciales con cota para podar
    
    NO es B&B si:
    - Solo tiene recursión con condiciones (eso es backtracking)
    - No tiene tracking de mejor solución
    - No tiene comparación con cotas
    
    B&B es MUY raro en pseudocódigo académico simple.
    La mayoría de algoritmos que parecen B&B son en realidad backtracking.
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.BRANCH_AND_BOUND
        self.pattern_name = "Branch and Bound"
        self.description = "Exploración con cotas y poda por optimalidad"
        self.typical_complexity = "Variable (depende de poda)"

        self._indicators = [
            PatternIndicator(
                "bound_tracking", 
                "Tracking de cotas (upper/lower bound)", 
                False, 
                5.0  # MUY CRÍTICO
            ),
            PatternIndicator(
                "best_solution_tracking", 
                "Tracking de mejor solución encontrada", 
                False, 
                5.0  # MUY CRÍTICO
            ),
            PatternIndicator(
                "pruning_by_bound", 
                "Poda basada en comparación con cota", 
                False, 
                4.5  # MUY IMPORTANTE
            ),
            PatternIndicator(
                "branch_exploration", 
                "Exploración de ramas del árbol", 
                False, 
                3.0
            ),
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta Branch and Bound con CRITERIOS ESTRICTOS"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. Tracking de cotas (CRÍTICO)
        bound_tracking = self._indicators[0]
        if analysis["has_bound_tracking"]:
            bound_tracking.found = True
            bound_tracking.evidence = f"Variables de cota detectadas: {', '.join(analysis['bound_vars'])}"
            indicators_found.append(bound_tracking)
        else:
            indicators_missing.append(bound_tracking)

        # 2. Tracking de mejor solución (CRÍTICO)
        best_tracking = self._indicators[1]
        if analysis["has_best_tracking"]:
            best_tracking.found = True
            best_tracking.evidence = f"Variables best detectadas: {', '.join(analysis['best_vars'])}"
            indicators_found.append(best_tracking)
        else:
            indicators_missing.append(best_tracking)

        # 3. Poda por cota (CRÍTICO)
        pruning = self._indicators[2]
        if analysis["has_bound_pruning"]:
            pruning.found = True
            pruning.evidence = "Comparaciones con cotas detectadas"
            indicators_found.append(pruning)
        else:
            indicators_missing.append(pruning)

        # 4. Exploración de ramas
        branch_exp = self._indicators[3]
        if analysis["has_branching"]:
            branch_exp.found = True
            branch_exp.evidence = "Estructura de exploración detectada"
            indicators_found.append(branch_exp)
        else:
            indicators_missing.append(branch_exp)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)

        # REGLAS ESTRICTAS
        # Si NO tiene los 3 indicadores críticos, NO es B&B
        if not (analysis["has_bound_tracking"] and 
                analysis["has_best_tracking"] and 
                analysis["has_bound_pruning"]):
            confidence = min(confidence * 0.05, 0.10)  # Máximo 10%
            reasoning = (
                "NO es Branch and Bound: falta tracking de cotas y/o mejor solución. "
                "B&B requiere comparación explícita con bounds para poda. "
                "Esto parece ser backtracking simple."
            )
        else:
            reasoning = self._build_reasoning(analysis)

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Análisis MUY estricto de B&B"""
        algo_name = get_algorithm_name(ast)

        analysis = {
            "has_bound_tracking": False,
            "has_best_tracking": False,
            "has_bound_pruning": False,
            "has_branching": False,
            "bound_vars": [],
            "best_vars": [],
        }

        # Buscar variables de cota
        bound_keywords = {'bound', 'upper', 'lower', 'limit', 'cota'}
        best_keywords = {'best', 'optimal', 'min_cost', 'max_profit', 'mejor'}
        
        all_vars = self._collect_all_variables(ast)
        
        # Detectar variables de cota
        for var in all_vars:
            var_lower = var.lower()
            if any(kw in var_lower for kw in bound_keywords):
                analysis["bound_vars"].append(var)
        
        # Detectar variables de mejor solución
        for var in all_vars:
            var_lower = var.lower()
            if any(kw in var_lower for kw in best_keywords):
                analysis["best_vars"].append(var)
        
        analysis["has_bound_tracking"] = len(analysis["bound_vars"]) > 0
        analysis["has_best_tracking"] = len(analysis["best_vars"]) > 0

        # Buscar comparaciones con cotas (poda)
        if analysis["bound_vars"]:
            analysis["has_bound_pruning"] = self._has_bound_comparisons(
                ast, 
                analysis["bound_vars"]
            )

        # Verificar si tiene estructura de branching
        if algo_name:
            result = PatternMatcher.has_backtracking_pattern(ast, algo_name)
            analysis["has_branching"] = result.matched

        return analysis

    def _collect_all_variables(self, node: ASTNode) -> set:
        """Colecta todos los nombres de variables en el AST"""
        variables = set()
        
        def _traverse(n: ASTNode):
            if isinstance(n, VariableNode):
                variables.add(n.name)
            elif isinstance(n, AssignmentNode):
                if hasattr(n.target, 'name'):
                    variables.add(n.target.name)
            
            for child in get_node_children(n):
                _traverse(child)
        
        _traverse(node)
        return variables

    def _has_bound_comparisons(self, node: ASTNode, bound_vars: list) -> bool:
        """
        Busca comparaciones con variables de cota.
        
        Patrón típico de B&B:
        if current_cost < best_bound then
            prune
        """
        def _search(n: ASTNode) -> bool:
            if isinstance(n, IfStatementNode):
                condition = n.condition
                if isinstance(condition, BinaryOpNode):
                    # Verificar si compara con variable de cota
                    left_var = self._get_variable_name(condition.left)
                    right_var = self._get_variable_name(condition.right)
                    
                    if left_var in bound_vars or right_var in bound_vars:
                        return True
            
            for child in get_node_children(n):
                if _search(child):
                    return True
            return False
        
        return _search(node)

    def _get_variable_name(self, node: ASTNode) -> str:
        """Extrae nombre de variable de un nodo"""
        if isinstance(node, VariableNode):
            return node.name
        return ""

    def _build_reasoning(self, analysis: Dict[str, Any]) -> str:
        """Construye razonamiento para B&B verdadero"""
        return (
            f"El algoritmo parece usar Branch and Bound: "
            f"tiene tracking de cotas ({', '.join(analysis['bound_vars'])}), "
            f"tracking de mejor solución ({', '.join(analysis['best_vars'])}), "
            f"y poda basada en comparación con bounds. "
            f"Esto es característico de B&B para problemas de optimización."
        )