"""
Cálculo de Cotas Fuertes (Tight Bounds)

Determina si Big O = Omega para obtener Theta (cota ajustada).
También calcula little-o y little-omega para análisis más detallado.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class TightBoundResult:
    """Resultado del análisis de cotas fuertes"""
    has_tight_bound: bool
    theta: Optional[str]
    big_o: str
    omega: str
    little_o: Optional[str] = None
    little_omega: Optional[str] = None
    explanation: str = ""
    confidence: float = 1.0


class TightBoundsCalculator:
    """
    Calculador de cotas fuertes.
    
    Determina si existe Theta (Big O = Omega) y calcula little-o y little-omega.
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        
        # Orden de complejidades (de menor a mayor)
        self.complexity_order = {
            "1": 0,
            "log n": 1,
            "log² n": 2,
            "√n": 3,
            "n": 4,
            "n log n": 5,
            "n²": 6,
            "n² log n": 7,
            "n³": 8,
            "2^n": 9,
            "n!": 10,
        }
    
    def calculate_tight_bounds(
        self,
        big_o: str,
        omega: str
    ) -> TightBoundResult:
        """
        Calcula cotas fuertes dado Big O y Omega.
        
        Args:
            big_o: Complejidad Big O (peor caso)
            omega: Complejidad Omega (mejor caso)
        
        Returns:
            TightBoundResult: Resultado del análisis
        """
        self.logger.info(f"Calculando cotas fuertes: O={big_o}, Ω={omega}")
        
        # Normalizar complejidades
        big_o_normalized = self._normalize_complexity(big_o)
        omega_normalized = self._normalize_complexity(omega)
        
        # Verificar si son iguales (cota ajustada)
        if big_o_normalized == omega_normalized:
            theta = f"Θ({big_o_normalized})"
            
            return TightBoundResult(
                has_tight_bound=True,
                theta=theta,
                big_o=big_o,
                omega=omega,
                explanation=(
                    f"El algoritmo tiene cota ajustada {theta} porque "
                    f"el peor caso y el mejor caso coinciden."
                )
            )
        
        # No hay cota ajustada
        return TightBoundResult(
            has_tight_bound=False,
            theta=None,
            big_o=big_o,
            omega=omega,
            explanation=(
                f"No existe cota ajustada porque O({big_o_normalized}) ≠ Ω({omega_normalized}). "
                f"El comportamiento varía entre {omega} en el mejor caso "
                f"y {big_o} en el peor caso."
            )
        )
    
    def calculate_little_notations(
        self,
        big_o: str,
        omega: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Calcula little-o y little-omega.
        
        little-o: f(n) ∈ o(g(n)) si f(n) crece estrictamente más lento que g(n)
        little-omega: f(n) ∈ ω(g(n)) si f(n) crece estrictamente más rápido que g(n)
        
        Args:
            big_o: Complejidad Big O
            omega: Complejidad Omega
        
        Returns:
            Tuple[little_o, little_omega]
        """
        big_o_norm = self._normalize_complexity(big_o)
        omega_norm = self._normalize_complexity(omega)
        
        # little-o: siguiente complejidad más grande que Big O
        little_o = self._get_next_complexity(big_o_norm)
        
        # little-omega: complejidad anterior más pequeña que Omega
        little_omega = self._get_prev_complexity(omega_norm)
        
        return (
            f"o({little_o})" if little_o else None,
            f"ω({little_omega})" if little_omega else None
        )
    
    def verify_tight_bound_conditions(
        self,
        complexity: str,
        lower_bound: str,
        upper_bound: str
    ) -> bool:
        """
        Verifica las condiciones para que exista cota ajustada.
        
        Para que f(n) ∈ Θ(g(n)):
        - f(n) ∈ O(g(n)) (cota superior)
        - f(n) ∈ Ω(g(n)) (cota inferior)
        
        Args:
            complexity: Complejidad real del algoritmo
            lower_bound: Cota inferior (Omega)
            upper_bound: Cota superior (Big O)
        
        Returns:
            bool: True si existe cota ajustada
        """
        complexity_norm = self._normalize_complexity(complexity)
        lower_norm = self._normalize_complexity(lower_bound)
        upper_norm = self._normalize_complexity(upper_bound)
        
        complexity_order = self._get_complexity_rank(complexity_norm)
        lower_order = self._get_complexity_rank(lower_norm)
        upper_order = self._get_complexity_rank(upper_norm)
        
        # Verificar que lower ≤ complexity ≤ upper
        return lower_order <= complexity_order <= upper_order
    
    def compare_complexities(
        self,
        complexity1: str,
        complexity2: str
    ) -> str:
        """
        Compara dos complejidades.
        
        Args:
            complexity1: Primera complejidad
            complexity2: Segunda complejidad
        
        Returns:
            str: "<", "=", ">" o "?"
        """
        c1 = self._normalize_complexity(complexity1)
        c2 = self._normalize_complexity(complexity2)
        
        rank1 = self._get_complexity_rank(c1)
        rank2 = self._get_complexity_rank(c2)
        
        if rank1 < rank2:
            return "<"
        elif rank1 > rank2:
            return ">"
        elif rank1 == rank2:
            return "="
        else:
            return "?"
    
    def get_complexity_class(self, complexity: str) -> str:
        """
        Obtiene la clase de complejidad.
        
        Args:
            complexity: Complejidad a clasificar
        
        Returns:
            str: Nombre de la clase
        """
        complexity_norm = self._normalize_complexity(complexity)
        
        classes = {
            "1": "Constante",
            "log n": "Logarítmica",
            "log² n": "Log-cuadrática",
            "√n": "Sublineal",
            "n": "Lineal",
            "n log n": "Linealítmica",
            "n²": "Cuadrática",
            "n² log n": "Cuasi-cúbica",
            "n³": "Cúbica",
            "2^n": "Exponencial",
            "n!": "Factorial",
        }
        
        return classes.get(complexity_norm, "Desconocida")
    
    # Métodos privados
    
    def _normalize_complexity(self, complexity: str) -> str:
        """Normaliza una complejidad para comparación"""
        # Remover notación
        complexity = complexity.replace("O(", "").replace(")", "")
        complexity = complexity.replace("Ω(", "").replace(")", "")
        complexity = complexity.replace("Θ(", "").replace(")", "")
        
        # Normalizar sintaxis
        complexity = complexity.replace("n^2", "n²")
        complexity = complexity.replace("n^3", "n³")
        complexity = complexity.replace("log^2 n", "log² n")
        complexity = complexity.replace("sqrt n", "√n")
        complexity = complexity.replace("sqrt(n)", "√n")
        
        # Remover espacios
        complexity = complexity.replace(" ", "")
        
        # Casos especiales
        if complexity == "nlogn":
            return "n log n"
        if complexity == "n*logn":
            return "n log n"
        
        return complexity.strip()
    
    def _get_complexity_rank(self, complexity: str) -> int:
        """Obtiene el rango de una complejidad"""
        return self.complexity_order.get(complexity, 999)
    
    def _get_next_complexity(self, complexity: str) -> Optional[str]:
        """Obtiene la siguiente complejidad más grande"""
        rank = self._get_complexity_rank(complexity)
        
        for comp, comp_rank in self.complexity_order.items():
            if comp_rank == rank + 1:
                return comp
        
        return None
    
    def _get_prev_complexity(self, complexity: str) -> Optional[str]:
        """Obtiene la complejidad anterior más pequeña"""
        rank = self._get_complexity_rank(complexity)
        
        if rank <= 0:
            return None
        
        for comp, comp_rank in self.complexity_order.items():
            if comp_rank == rank - 1:
                return comp
        
        return None
    
    def generate_bounds_report(
        self,
        result: TightBoundResult
    ) -> Dict:
        """
        Genera un reporte detallado de cotas.
        
        Args:
            result: Resultado del análisis
        
        Returns:
            Dict: Reporte estructurado
        """
        report = {
            "has_tight_bound": result.has_tight_bound,
            "complexity_class": self.get_complexity_class(result.big_o),
            "bounds": {
                "big_o": result.big_o,
                "omega": result.omega,
                "theta": result.theta,
                "little_o": result.little_o,
                "little_omega": result.little_omega,
            },
            "explanation": result.explanation,
            "confidence": result.confidence,
        }
        
        # Agregar comparación
        comparison = self.compare_complexities(result.big_o, result.omega)
        report["bounds_comparison"] = {
            "relation": comparison,
            "description": self._get_comparison_description(comparison)
        }
        
        return report
    
    def _get_comparison_description(self, relation: str) -> str:
        """Obtiene descripción de la comparación"""
        descriptions = {
            "<": "El peor caso es más eficiente que el mejor caso (inconsistente)",
            "=": "El peor caso y el mejor caso coinciden (cota ajustada)",
            ">": "El peor caso es menos eficiente que el mejor caso (esperado)",
            "?": "No se puede comparar"
        }
        return descriptions.get(relation, "Desconocido")


def calculate_tight_bounds(big_o: str, omega: str) -> TightBoundResult:
    """
    Helper function para calcular cotas fuertes.
    
    Args:
        big_o: Complejidad Big O
        omega: Complejidad Omega
    
    Returns:
        TightBoundResult: Resultado del análisis
    """
    calculator = TightBoundsCalculator()
    return calculator.calculate_tight_bounds(big_o, omega)