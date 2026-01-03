"""
Motor Principal de Análisis

Orquesta todos los analizadores y proporciona un punto de entrada
unificado para el análisis de complejidad.
"""

from typing import Dict, Optional
from dataclasses import dataclass, field

from app.core.parser.ast_nodes import ProgramNode
from app.core.analyzer.complexity.complexity_calculator import ComplexityCalculator
from app.core.analyzer.line_by_line_analyzer import LineByLineAnalyzer, LineByLineResult
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class AnalysisResult:
    """Resultado completo del análisis"""
    algorithm_name: str
    
    # Complejidades
    big_o: str
    omega: str
    theta: str
    
    # Análisis línea por línea
    line_by_line: Optional[LineByLineResult] = None
    
    # Información adicional
    is_recursive: bool = False
    max_nesting_depth: int = 0
    
    # Metadatos
    analysis_time: float = 0.0
    
    def to_dict(self) -> dict:
        """Convierte a diccionario"""
        return {
            "algorithm_name": self.algorithm_name,
            "complexity": {
                "big_o": self.big_o,
                "omega": self.omega,
                "theta": self.theta
            },
            "line_by_line": self.line_by_line.to_dict() if self.line_by_line else None,
            "metadata": {
                "is_recursive": self.is_recursive,
                "max_nesting_depth": self.max_nesting_depth,
                "analysis_time": self.analysis_time
            }
        }

class AnalyzerEngine:
    """
    Motor principal de análisis.
    
    Orquesta todos los analizadores para generar un análisis completo.
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        
        # Inicializar analizadores
        self.complexity_calculator = ComplexityCalculator()
        self.line_by_line_analyzer = LineByLineAnalyzer()
    
    def analyze(
        self,
        ast: ProgramNode,
        analyze_line_by_line: bool = True
    ) -> AnalysisResult:
        """
        Analiza un algoritmo completamente.
        
        Args:
            ast: AST del algoritmo
            analyze_line_by_line: Si debe hacer análisis línea por línea
        
        Returns:
            AnalysisResult: Resultado completo del análisis
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Iniciando análisis completo: {ast.algorithm.name}")
        
        try:
            # 1. Análisis de complejidad
            complexity_results = self.complexity_calculator.analyze_all(ast)
            
            # 2. Análisis línea por línea (opcional)
            line_by_line_result = None
            if analyze_line_by_line:
                line_by_line_result = self.line_by_line_analyzer.analyze(ast)
            
            # 3. Información adicional (TODO: implementar)
            is_recursive = False  # TODO: detectar recursión
            max_nesting_depth = 0  # TODO: calcular profundidad
            
            # Calcular tiempo
            analysis_time = time.time() - start_time
            
            # Crear resultado
            result = AnalysisResult(
                algorithm_name=ast.algorithm.name,
                big_o=complexity_results["big_o"],
                omega=complexity_results["omega"],
                theta=complexity_results["theta"],
                line_by_line=line_by_line_result,
                is_recursive=is_recursive,
                max_nesting_depth=max_nesting_depth,
                analysis_time=analysis_time
            )
            
            self.logger.info(
                f"Análisis completado en {analysis_time:.3f}s: "
                f"O={result.big_o}, Ω={result.omega}, Θ={result.theta}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error en análisis: {e}")
            raise