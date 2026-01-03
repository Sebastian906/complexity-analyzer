"""
Calculador de Complejidad - Orquestador Principal

Coordina todos los analizadores de complejidad (O, Ω, Θ)
y proporciona un análisis completo.
"""

from typing import Dict

from app.core.analyzer.complexity.big_o_analyzer import BigOAnalyzer
from app.core.analyzer.complexity.omega_analyzer import OmegaAnalyzer
from app.core.analyzer.complexity.theta_analyzer import ThetaAnalyzer
from app.core.parser.ast_nodes import ProgramNode
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ComplexityCalculator:
    """Orquestador principal de análisis de complejidad"""
    
    def __init__(self):
        self.big_o_analyzer = BigOAnalyzer()
        self.omega_analyzer = OmegaAnalyzer()
        self.theta_analyzer = ThetaAnalyzer()
        
        logger.info("ComplexityCalculator inicializado")
    
    def analyze_all(self, ast: ProgramNode) -> Dict[str, str]:
        """
        Analiza todas las complejidades del algoritmo.
        
        Args:
            ast: AST del algoritmo
        
        Returns:
            Dict con big_o, omega, theta
        """
        results = {}
        
        logger.info(f"Analizando algoritmo: {ast.algorithm.name}")
        
        # Big O
        big_o_result = self.big_o_analyzer.analyze(ast)
        results["big_o"] = str(big_o_result)
        
        # Omega
        omega_result = self.omega_analyzer.analyze(ast)
        results["omega"] = str(omega_result)
        
        # Theta
        theta_result = self.theta_analyzer.analyze(ast)
        results["theta"] = str(theta_result)
        
        logger.info(f"Análisis completado: {results}")
        
        return results