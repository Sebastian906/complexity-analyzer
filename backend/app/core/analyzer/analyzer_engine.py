"""
Motor Principal de Análisis

Orquesta todos los analizadores incluyendo ecuaciones de recurrencia
y proporciona un punto de entrada unificado para el análisis completo.
"""

from typing import Dict, Optional
from dataclasses import dataclass, field
import time

from app.core.parser.ast_nodes import ProgramNode
from app.core.analyzer.complexity.complexity_calculator import ComplexityCalculator
from app.core.analyzer.complexity.tight_bounds import TightBoundsCalculator, TightBoundResult
from app.core.analyzer.line_by_line_analyzer import LineByLineAnalyzer, LineByLineResult
from app.core.analyzer.space_analyzer import SpaceAnalyzer, SpaceAnalysisResult
from app.core.analyzer.recurrence.recurrence_builder import (
    RecurrenceBuilder,
    RecurrenceEquation
)
from app.core.analyzer.recurrence.temporal_complexity import (
    TemporalComplexityAnalyzer,
    TemporalComplexityResult
)
from app.core.analyzer.recurrence.spatial_complexity import (
    SpatialComplexityAnalyzer,
    SpatialComplexityResult
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class AnalysisResult:
    """Resultado completo del análisis"""
    algorithm_name: str
    
    # Complejidades básicas
    big_o: str
    omega: str
    theta: str
    
    # Análisis línea por línea
    line_by_line: Optional[LineByLineResult] = None
    
    # Análisis espacial
    space_analysis: Optional[SpaceAnalysisResult] = None
    
    # Cotas fuertes
    tight_bounds: Optional[TightBoundResult] = None
    
    # Ecuaciones de recurrencia
    temporal_recurrence: Optional[TemporalComplexityResult] = None
    spatial_recurrence: Optional[SpatialComplexityResult] = None
    
    # Información adicional
    is_recursive: bool = False
    max_nesting_depth: int = 0
    
    # Metadatos
    analysis_time: float = 0.0
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para serialización"""
        result = {
            "algorithm_name": self.algorithm_name,
            "complexity": {
                "temporal": {
                    "big_o": self.big_o,
                    "omega": self.omega,
                    "theta": self.theta
                },
                "spatial": self.space_analysis.to_dict() if self.space_analysis else None
            },
            "line_by_line": self.line_by_line.to_dict() if self.line_by_line else None,
            "tight_bounds": None,
            "recurrence_equations": {
                "temporal": self.temporal_recurrence.to_dict() if self.temporal_recurrence else None,
                "spatial": self.spatial_recurrence.to_dict() if self.spatial_recurrence else None
            },
            "metadata": {
                "is_recursive": self.is_recursive,
                "max_nesting_depth": self.max_nesting_depth,
                "analysis_time": self.analysis_time
            }
        }
        
        # Agregar tight bounds si existe
        if self.tight_bounds:
            result["tight_bounds"] = {
                "has_tight_bound": self.tight_bounds.has_tight_bound,
                "theta": self.tight_bounds.theta,
                "explanation": self.tight_bounds.explanation,
                "little_o": self.tight_bounds.little_o,
                "little_omega": self.tight_bounds.little_omega
            }
        
        return result


class AnalyzerEngine:
    """
    Motor principal de análisis - Versión Completa.
    
    Orquesta todos los analizadores para generar un análisis exhaustivo
    incluyendo ecuaciones de recurrencia.
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        
        # Inicializar analizadores básicos
        self.complexity_calculator = ComplexityCalculator()
        self.line_by_line_analyzer = LineByLineAnalyzer()
        self.space_analyzer = SpaceAnalyzer()
        self.tight_bounds_calculator = TightBoundsCalculator()
        
        # Inicializar analizadores de recurrencia
        self.recurrence_builder = RecurrenceBuilder()
        self.temporal_analyzer = TemporalComplexityAnalyzer()
        self.spatial_complexity_analyzer = SpatialComplexityAnalyzer()
    
    def analyze(
        self,
        ast: ProgramNode,
        analyze_line_by_line: bool = True,
        analyze_space: bool = True,
        analyze_recurrence: bool = True,
        analyze_tight_bounds: bool = True
    ) -> AnalysisResult:
        """
        Analiza un algoritmo completamente.
        
        Args:
            ast: AST del algoritmo
            analyze_line_by_line: Análisis línea por línea
            analyze_space: Análisis de complejidad espacial
            analyze_recurrence: Análisis de ecuaciones de recurrencia
            analyze_tight_bounds: Verificación de cotas ajustadas
        
        Returns:
            AnalysisResult: Resultado completo del análisis
        """
        start_time = time.time()
        
        self.logger.info(f"=== Iniciando análisis completo: {ast.algorithm.name} ===")
        
        try:
            # 1. ANÁLISIS DE COMPLEJIDAD TEMPORAL BÁSICO
            self.logger.info("1/5 Analizando complejidad temporal...")
            complexity_results = self.complexity_calculator.analyze_all(ast)
            
            big_o = complexity_results["big_o"]
            omega = complexity_results["omega"]
            theta = complexity_results["theta"]
            
            self.logger.info(f"  Big O: {big_o}")
            self.logger.info(f"  Omega: {omega}")
            self.logger.info(f"  Theta: {theta}")
            
            # 2. ANÁLISIS LÍNEA POR LÍNEA
            line_by_line_result = None
            if analyze_line_by_line:
                self.logger.info("2/5 Analizando línea por línea...")
                line_by_line_result = self.line_by_line_analyzer.analyze(ast)
                self.logger.info(f"  Analizadas {len(line_by_line_result.lines)} líneas")
            
            # 3. ANÁLISIS ESPACIAL
            space_analysis_result = None
            if analyze_space:
                self.logger.info("3/5 Analizando complejidad espacial...")
                space_analysis_result = self.space_analyzer.analyze(ast)
                self.logger.info(f"  S(n) = {space_analysis_result.space_complexity}")
            
            # 4. COTAS AJUSTADAS (TIGHT BOUNDS)
            tight_bounds_result = None
            if analyze_tight_bounds:
                self.logger.info("4/5 Verificando cotas ajustadas...")
                tight_bounds_result = self.tight_bounds_calculator.calculate_tight_bounds(
                    big_o,
                    omega
                )
                if tight_bounds_result.has_tight_bound:
                    self.logger.info(f"  ✓ Cota ajustada: {tight_bounds_result.theta}")
                else:
                    self.logger.info(f"  ✗ No existe cota ajustada")
            
            # 5. ECUACIONES DE RECURRENCIA
            temporal_recurrence_result = None
            spatial_recurrence_result = None
            is_recursive = False
            
            if analyze_recurrence:
                self.logger.info("5/5 Construyendo ecuaciones de recurrencia...")
                
                # Construir ecuaciones T(n) y S(n)
                temporal_eq = self.recurrence_builder.build_temporal_recurrence(
                    ast,
                    ast.algorithm.name
                )
                
                spatial_eq = self.recurrence_builder.build_spatial_recurrence(
                    ast,
                    ast.algorithm.name
                )
                
                if temporal_eq and temporal_eq.is_recursive:
                    is_recursive = True
                    self.logger.info(f"  T(n): {temporal_eq.equation}")
                    
                    # Resolver T(n)
                    temporal_recurrence_result = self.temporal_analyzer.analyze_temporal_complexity(
                        temporal_eq,
                        fallback_complexity=self._extract_complexity(big_o)
                    )
                    
                    if temporal_recurrence_result.solution:
                        self.logger.info(
                            f"  Método: {temporal_recurrence_result.solution.method_used.value}"
                        )
                
                if spatial_eq and spatial_eq.is_recursive:
                    self.logger.info(f"  S(n): {spatial_eq.equation}")
                    
                    # Resolver S(n)
                    input_space = space_analysis_result.input_space if space_analysis_result else "n"
                    aux_space = space_analysis_result.auxiliary_space if space_analysis_result else "1"
                    
                    spatial_recurrence_result = self.spatial_complexity_analyzer.analyze_spatial_complexity(
                        spatial_eq,
                        input_space=self._extract_complexity(input_space),
                        auxiliary_space=self._extract_complexity(aux_space)
                    )
            
            # Calcular tiempo de análisis
            analysis_time = time.time() - start_time
            
            # Detectar recursión (fallback si no se detectó en recurrencias)
            if not is_recursive:
                is_recursive = self._detect_recursion_simple(ast)
            
            # Calcular profundidad de anidación
            max_nesting_depth = self._calculate_nesting_depth(ast.algorithm.body)
            
            # Crear resultado
            result = AnalysisResult(
                algorithm_name=ast.algorithm.name,
                big_o=big_o,
                omega=omega,
                theta=theta,
                line_by_line=line_by_line_result,
                space_analysis=space_analysis_result,
                tight_bounds=tight_bounds_result,
                temporal_recurrence=temporal_recurrence_result,
                spatial_recurrence=spatial_recurrence_result,
                is_recursive=is_recursive,
                max_nesting_depth=max_nesting_depth,
                analysis_time=analysis_time
            )
            
            self.logger.info(f"=== Análisis completado en {analysis_time:.3f}s ===")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error en análisis: {e}", exc_info=True)
            raise
    
    def analyze_from_code(
        self,
        pseudocode: str,
        **kwargs
    ) -> AnalysisResult:
        """
        Analiza un algoritmo desde código pseudocódigo.
        
        Args:
            pseudocode: Código en pseudocódigo
            **kwargs: Opciones de análisis
        
        Returns:
            AnalysisResult
        """
        from app.core.parser import parse_pseudocode
        
        ast = parse_pseudocode(pseudocode)
        return self.analyze(ast, **kwargs)
    
    def get_complexity_summary(self, result: AnalysisResult) -> str:
        """
        Genera un resumen legible del análisis.
        
        Args:
            result: Resultado del análisis
        
        Returns:
            str: Resumen formateado
        """
        lines = []
        
        lines.append(f"ANÁLISIS DE COMPLEJIDAD: {result.algorithm_name}")
        lines.append("=" * 60)
        lines.append("")
        
        # Complejidad Temporal
        lines.append("COMPLEJIDAD TEMPORAL:")
        lines.append(f"  Peor caso (Big O):      {result.big_o}")
        lines.append(f"  Mejor caso (Omega):     {result.omega}")
        
        if result.theta:
            lines.append(f"  Caso promedio (Theta):  {result.theta}")
        else:
            lines.append(f"  Caso promedio (Theta):  No existe (O ≠ Ω)")
        
        # Ecuación de recurrencia temporal
        if result.temporal_recurrence and result.temporal_recurrence.recurrence_equation:
            lines.append("")
            lines.append("ECUACIÓN DE RECURRENCIA TEMPORAL:")
            lines.append(f"  {result.temporal_recurrence.recurrence_equation.equation}")
            
            if result.temporal_recurrence.solution:
                lines.append(f"  Método: {result.temporal_recurrence.solution.method_used.value}")
                lines.append(f"  Solución: T(n) = {result.temporal_recurrence.solution.complexity}")
        
        lines.append("")
        
        # Complejidad Espacial
        if result.space_analysis:
            lines.append("COMPLEJIDAD ESPACIAL:")
            lines.append(f"  Total: {result.space_analysis.space_complexity}")
            lines.append(f"  - Entrada:   {result.space_analysis.input_space}")
            lines.append(f"  - Auxiliar:  {result.space_analysis.auxiliary_space}")
            lines.append(f"  - Recursión: {result.space_analysis.recursion_space}")
        
        # Ecuación de recurrencia espacial
        if result.spatial_recurrence and result.spatial_recurrence.recurrence_equation:
            lines.append("")
            lines.append("ECUACIÓN DE RECURRENCIA ESPACIAL:")
            lines.append(f"  {result.spatial_recurrence.recurrence_equation.equation}")
            
            if result.spatial_recurrence.solution:
                lines.append(f"  Método: {result.spatial_recurrence.solution.method_used.value}")
                lines.append(f"  Solución: S(n) = {result.spatial_recurrence.solution.complexity}")
        
        lines.append("")
        
        # Metadatos
        lines.append("INFORMACIÓN ADICIONAL:")
        lines.append(f"  Recursivo: {'Sí' if result.is_recursive else 'No'}")
        
        if result.tight_bounds:
            if result.tight_bounds.has_tight_bound:
                lines.append(f"  Cota ajustada: Sí ({result.tight_bounds.theta})")
            else:
                lines.append(f"  Cota ajustada: No")
        
        lines.append(f"  Tiempo de análisis: {result.analysis_time:.3f}s")
        
        return "\n".join(lines)
    
    # Métodos auxiliares
    
    def _extract_complexity(self, complexity_str: str) -> str:
        """Extrae la complejidad sin la notación O()"""
        return complexity_str.replace("O(", "").replace(")", "").replace("Θ(", "").replace("Ω(", "")
    
    def _detect_recursion_simple(self, ast: ProgramNode) -> bool:
        """Detección robusta de recursión"""
        from app.core.parser.ast_nodes import (
            BlockNode, CallStatementNode, ForLoopNode, 
            WhileLoopNode, IfStatementNode, RepeatLoopNode
        )
        
        algorithm_name = ast.algorithm.name
        
        def check_node(node) -> bool:
            """Revisa un nodo recursivamente buscando llamadas al algoritmo"""
            if node is None:
                return False
            
            if isinstance(node, CallStatementNode):
                if node.function_name == algorithm_name:
                    return True
            
            elif isinstance(node, BlockNode):
                for stmt in node.statements:
                    if check_node(stmt):
                        return True
            
            elif isinstance(node, ForLoopNode):
                if check_node(node.body):
                    return True
            
            elif isinstance(node, WhileLoopNode):
                if check_node(node.body):
                    return True
            
            elif isinstance(node, RepeatLoopNode):
                for stmt in node.body:
                    if check_node(stmt):
                        return True
            
            elif isinstance(node, IfStatementNode):
                if check_node(node.then_block):
                    return True
                if node.else_block and check_node(node.else_block):
                    return True
            
            return False
        
        return check_node(ast.algorithm.body)
    
    def _calculate_nesting_depth(self, node, current_depth: int = 0) -> int:
        """Calcula la profundidad máxima de anidación de estructuras de control"""
        from app.core.parser.ast_nodes import (
            BlockNode, ForLoopNode, WhileLoopNode, 
            IfStatementNode, RepeatLoopNode
        )
        
        if node is None:
            return current_depth
        
        max_depth = current_depth
        
        if isinstance(node, BlockNode):
            for stmt in node.statements:
                depth = self._calculate_nesting_depth(stmt, current_depth)
                max_depth = max(max_depth, depth)
        
        elif isinstance(node, (ForLoopNode, WhileLoopNode)):
            # Incrementar profundidad para loops
            body_depth = self._calculate_nesting_depth(node.body, current_depth + 1)
            max_depth = max(max_depth, body_depth)
        
        elif isinstance(node, RepeatLoopNode):
            # Incrementar profundidad para repeat
            for stmt in node.body:
                depth = self._calculate_nesting_depth(stmt, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        elif isinstance(node, IfStatementNode):
            # Incrementar profundidad para if
            then_depth = self._calculate_nesting_depth(node.then_block, current_depth + 1)
            max_depth = max(max_depth, then_depth)
            
            if node.else_block:
                else_depth = self._calculate_nesting_depth(node.else_block, current_depth + 1)
                max_depth = max(max_depth, else_depth)
        
        return max_depth