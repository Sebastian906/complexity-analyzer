"""
Backtracking Detector - Detecta algoritmos de Backtracking

Identifica algoritmos que exploran soluciones mediante prueba y error,
retrocediendo cuando una solución no es válida.
"""

from typing import Dict, Any

from app.core.parser.ast_nodes import (
    ASTNode, AlgorithmNode, IfStatementNode, 
    CallStatementNode, AssignmentNode, ReturnStatementNode,
    BinaryOpNode, ForLoopNode, WhileLoopNode, BlockNode
)
from app.core.patterns.base_pattern import (
    BasePatternDetector,
    PatternType,
    PatternIndicator,
    PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_algorithm_name, get_node_children

class BacktrackingDetector(BasePatternDetector):
    """Detector de Backtracking MEJORADO - Corregido"""

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.BACKTRACKING
        self.pattern_name = "Backtracking"
        self.description = "Exploración exhaustiva con retroceso y poda"
        self.typical_complexity = "O(2^n) o O(n!)"

        self._indicators = [
            PatternIndicator(
                name="loop_over_candidates",
                description="Loop que itera sobre candidatos/opciones",
                found=False,
                weight=6.0
            ),
            PatternIndicator(
                name="recursive_exploration",
                description="Llamada recursiva dentro del loop",
                found=False,
                weight=6.0
            ),
            PatternIndicator(
                name="state_reversal",
                description="Reversión de estado después de recursión",
                found=False,
                weight=5.0
            ),
            PatternIndicator(
                name="candidate_validation",
                description="Validación de candidatos",
                found=False,
                weight=3.5
            ),
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta patrón de backtracking"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. Loop sobre candidatos (CRÍTICO)
        loop_cand = self._indicators[0]
        if analysis["has_candidate_loop"]:
            loop_cand.found = True
            loop_cand.evidence = "Loop que itera sobre opciones detectado"
            indicators_found.append(loop_cand)
        else:
            indicators_missing.append(loop_cand)

        # 2. Recursión dentro del loop (CRÍTICO)
        rec_exp = self._indicators[1]
        if analysis["has_recursive_in_loop"]:
            rec_exp.found = True
            rec_exp.evidence = f"Llamadas recursivas dentro de loop: {analysis['recursive_calls']}"
            indicators_found.append(rec_exp)
        else:
            indicators_missing.append(rec_exp)

        # 3. Reversión de estado (CRÍTICO - diferenciador clave)
        reversal = self._indicators[2]
        if analysis["has_state_reversal"]:
            reversal.found = True
            reversal.evidence = f"{analysis['reversal_count']} reversiones de estado detectadas"
            indicators_found.append(reversal)
        else:
            indicators_missing.append(reversal)

        # 4. Validación de candidatos
        validation = self._indicators[3]
        if analysis["has_validation"]:
            validation.found = True
            validation.evidence = "Validación de candidatos detectada"
            indicators_found.append(validation)
        else:
            indicators_missing.append(validation)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)

        # REGLAS ESTRICTAS
        # Los 3 primeros indicadores son OBLIGATORIOS para backtracking
        critical_missing = []
        if not analysis["has_candidate_loop"]:
            critical_missing.append("loop sobre candidatos")
        if not analysis["has_recursive_in_loop"]:
            critical_missing.append("recursión en loop")
        if not analysis["has_state_reversal"]:
            critical_missing.append("reversión de estado")
        
        if critical_missing:
            # Sin indicadores críticos, NO es backtracking
            confidence = min(confidence * 0.15, 0.20)
            reasoning = f"NO es backtracking: falta {', '.join(critical_missing)}. "
        else:
            reasoning = ""

        reasoning += self._build_reasoning(analysis)

        # BOOST CRÍTICO: Si tiene los 3 primeros indicadores, ES backtracking
        if (analysis["has_candidate_loop"] and 
            analysis["has_recursive_in_loop"] and 
            analysis["has_state_reversal"]):
            confidence = min(confidence * 1.8, 0.98)  # BOOST 80%

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning,
            **analysis
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Analiza estructura con foco en patrón backtracking"""
        algo_name = get_algorithm_name(ast)

        analysis = {
            "algorithm_name": algo_name,
            "has_candidate_loop": False,
            "has_recursive_in_loop": False,
            "has_state_reversal": False,
            "has_validation": False,
            "recursive_calls": 0,
            "reversal_count": 0,
        }

        # Buscar loops
        loops = self._find_candidate_loops(ast, algo_name)
        analysis["has_candidate_loop"] = len(loops) > 0
        
        if loops:
            # Verificar si hay recursión DENTRO de los loops
            for loop_node in loops:
                if self._has_recursion_in_node(loop_node, algo_name):
                    analysis["has_recursive_in_loop"] = True
                    break
        
        # Contar llamadas recursivas totales
        if algo_name:
            result = PatternMatcher.has_recursive_calls(ast, algo_name)
            analysis["recursive_calls"] = result.metadata.get("call_count", 0)

        # Detectar reversión de estado (PATRÓN CLAVE) - MEJORADO
        reversal_count = self._detect_state_reversal_improved(ast, algo_name)
        analysis["has_state_reversal"] = reversal_count > 0
        analysis["reversal_count"] = reversal_count

        # Detectar validación de candidatos
        analysis["has_validation"] = self._has_candidate_validation(ast)

        return analysis

    def _find_candidate_loops(self, node: ASTNode, func_name: str) -> list:
        """
        Encuentra loops que iteran sobre candidatos.
        
        En backtracking típico: for col in 1..n do (explorar todas las opciones)
        """
        loops = []
        
        def _search(n: ASTNode):
            if isinstance(n, (ForLoopNode, WhileLoopNode)):
                loops.append(n)
            
            for child in get_node_children(n):
                _search(child)
        
        _search(node)
        return loops

    def _has_recursion_in_node(self, node: ASTNode, func_name: str) -> bool:
        """Verifica si hay llamadas recursivas dentro de un nodo"""
        if isinstance(node, CallStatementNode):
            if node.function_name == func_name:
                return True
        
        for child in get_node_children(node):
            if self._has_recursion_in_node(child, func_name):
                return True
        
        return False

    def _detect_state_reversal_improved(self, node: ASTNode, func_name: str) -> int:
        """
        VERSIÓN MEJORADA: Detecta reversión de estado con búsqueda más flexible.
        
        Busca el patrón:
        1. Asignación a una variable/array
        2. Llamada recursiva
        3. Asignación a la MISMA variable/array (revertir)
        
        Ejemplo típico:
        board[row][col] ← 1         (asignar)
        call n_queens(...)           (explorar)
        board[row][col] ← 0         (revertir)
        """
        reversal_count = 0
        
        def _find_reversals_in_block(block_statements: list) -> int:
            """Busca reversiones en una lista de statements"""
            count = 0
            
            # Buscar secuencias de 3+ statements
            for i in range(len(block_statements) - 2):
                stmt1 = block_statements[i]
                stmt2 = block_statements[i + 1]
                stmt3 = block_statements[i + 2]
                
                # Patrón: Assignment → Call → Assignment
                if (isinstance(stmt1, AssignmentNode) and
                    isinstance(stmt2, CallStatementNode) and
                    isinstance(stmt3, AssignmentNode)):
                    
                    # Verificar que stmt2 es recursiva
                    if stmt2.function_name == func_name:
                        # Verificar que stmt1 y stmt3 modifican el mismo target
                        target1 = self._get_assignment_target_str(stmt1)
                        target3 = self._get_assignment_target_str(stmt3)
                        
                        if target1 and target3 and target1 == target3:
                            count += 1
            
            return count
        
        def _search_in_node(n: ASTNode) -> int:
            """Busca reversiones recursivamente en el AST"""
            count = 0
            
            # Buscar en BlockNode
            if isinstance(n, BlockNode):
                count += _find_reversals_in_block(n.statements)
            
            # Buscar en IfStatement (dentro del then_block)
            if isinstance(n, IfStatementNode):
                if isinstance(n.then_block, BlockNode):
                    count += _find_reversals_in_block(n.then_block.statements)
                if n.else_block and isinstance(n.else_block, BlockNode):
                    count += _find_reversals_in_block(n.else_block.statements)
            
            # Buscar en ForLoop
            if isinstance(n, ForLoopNode):
                if isinstance(n.body, BlockNode):
                    count += _find_reversals_in_block(n.body.statements)
            
            # Buscar en WhileLoop
            if isinstance(n, WhileLoopNode):
                if isinstance(n.body, BlockNode):
                    count += _find_reversals_in_block(n.body.statements)
            
            # Recursivamente buscar en hijos
            for child in get_node_children(n):
                count += _search_in_node(child)
            
            return count
        
        reversal_count = _search_in_node(node)
        return reversal_count

    def _get_assignment_target_str(self, assign_node: AssignmentNode) -> str:
        """
        Obtiene representación string del target de asignación.
        
        Ejemplos:
        - board[row][col] → "board"
        - x → "x"
        - arr[i] → "arr"
        """
        if not hasattr(assign_node, 'target'):
            return None
        
        target = assign_node.target
        
        # LValueNode: puede tener nombre e índices
        if hasattr(target, 'name'):
            return target.name
        
        # ArrayAccessNode: tiene array_name
        if hasattr(target, 'array_name'):
            return target.array_name
        
        return None

    def _has_candidate_validation(self, node: ASTNode) -> bool:
        """
        Detecta validación de candidatos.
        
        Busca llamadas a funciones como is_safe, is_valid, can_place, etc.
        """
        validation_keywords = {'safe', 'valid', 'can', 'check', 'verify'}
        
        def _search(n: ASTNode) -> bool:
            if isinstance(n, CallStatementNode):
                func_name_lower = n.function_name.lower()
                if any(kw in func_name_lower for kw in validation_keywords):
                    return True
            
            for child in get_node_children(n):
                if _search(child):
                    return True
            return False
        
        return _search(node)

    def _build_reasoning(self, analysis: Dict[str, Any]) -> str:
        """Construye razonamiento"""
        if not analysis["has_candidate_loop"]:
            return (
                "No se detectó loop sobre candidatos. "
                "Backtracking requiere iterar sobre todas las opciones posibles."
            )
        
        if not analysis["has_recursive_in_loop"]:
            return (
                "No se detectó recursión dentro del loop. "
                "Backtracking requiere exploración recursiva de cada candidato."
            )
        
        if not analysis["has_state_reversal"]:
            return (
                "No se detectó reversión de estado. "
                "Backtracking DEBE revertir cambios al retroceder (rollback). "
                "Sin reversión, probablemente es otro patrón."
            )
        
        return (
            f"El algoritmo usa Backtracking: "
            f"itera sobre candidatos, explora recursivamente, "
            f"y revierte estado ({analysis['reversal_count']} reversiones detectadas). "
            f"Esto es característico de backtracking con poda."
        )