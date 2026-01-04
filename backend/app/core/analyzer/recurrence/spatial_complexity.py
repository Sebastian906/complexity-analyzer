"""
Spatial Complexity - Wrapper especializado para S(n)

Proporciona interfaz especializada para ecuaciones de
complejidad espacial S(n).
"""

from typing import Optional
from dataclasses import dataclass

from app.core.analyzer.recurrence.recurrence_builder import RecurrenceEquation
from app.core.analyzer.recurrence.recurrence_solver import (
    RecurrenceSolver,
    SolutionResult,
    SolutionMethod
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class SpatialComplexityResult:
    """Resultado del análisis de complejidad espacial"""
    recurrence_equation: Optional[RecurrenceEquation]
    solution: Optional[SolutionResult]
    space_complexity: str
    input_space: str
    auxiliary_space: str
    recursion_space: str
    is_recursive: bool
    explanation: str

    def to_dict(self) -> dict:
        """Convierte a diccionario"""
        return {
            "recurrence_equation": {
                "equation": self.recurrence_equation.equation,
                "base_case": self.recurrence_equation.base_case,
                "pattern": self.recurrence_equation.recursion_pattern
            } if self.recurrence_equation else None,

            "solution": {
                "complexity": self.solution.complexity,
                "method": self.solution.method_used.value,
                "form": self.solution.form_detected.name,
                "steps": self.solution.steps
            } if self.solution else None,

            "space_complexity": self.space_complexity,
            "breakdown": {
                "input_space": self.input_space,
                "auxiliary_space": self.auxiliary_space,
                "recursion_space": self.recursion_space
            },
            "is_recursive": self.is_recursive,
            "explanation": self.explanation
        }

class SpatialComplexityAnalyzer:
    """
    Analizador especializado de complejidad espacial.

    Combina análisis de espacio auxiliar con resolución
    de ecuaciones de recurrencia S(n) para recursión.
    """

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.solver = RecurrenceSolver()

    def analyze_spatial_complexity(
        self,
        recurrence_eq: Optional[RecurrenceEquation],
        input_space: str = "n",
        auxiliary_space: str = "1"
    ) -> SpatialComplexityResult:
        """
        Analiza complejidad espacial completa.

        Args:
            recurrence_eq: Ecuación S(n) (si es recursivo)
            input_space: Espacio de entrada
            auxiliary_space: Espacio auxiliar

        Returns:
            SpatialComplexityResult
        """
        self.logger.info("Analizando complejidad espacial")

        # Si no es recursivo
        if not recurrence_eq or not recurrence_eq.is_recursive:
            total_space = self._combine_spaces(input_space, auxiliary_space, "1")

            return SpatialComplexityResult(
                recurrence_equation=None,
                solution=None,
                space_complexity=f"O({total_space})",
                input_space=f"O({input_space})",
                auxiliary_space=f"O({auxiliary_space})",
                recursion_space="O(1)",
                is_recursive=False,
                explanation=self._generate_non_recursive_explanation(
                    total_space, input_space, auxiliary_space
                )
            )

        # Resolver ecuación de recurrencia espacial
        try:
            solution = self.solver.solve(recurrence_eq.equation)

            recursion_space = solution.complexity

            # Espacio total = max(input, auxiliary, recursion)
            total_space = self._combine_spaces(
                input_space,
                auxiliary_space,
                recursion_space
            )

            explanation = self._generate_recursive_explanation(
                recurrence_eq,
                solution,
                total_space,
                input_space,
                auxiliary_space,
                recursion_space
            )

            return SpatialComplexityResult(
                recurrence_equation=recurrence_eq,
                solution=solution,
                space_complexity=f"O({total_space})",
                input_space=f"O({input_space})",
                auxiliary_space=f"O({auxiliary_space})",
                recursion_space=f"O({recursion_space})",
                is_recursive=True,
                explanation=explanation
            )

        except Exception as e:
            self.logger.error(f"Error resolviendo S(n): {e}")

            # Fallback
            total_space = self._combine_spaces(input_space, auxiliary_space, "n")

            return SpatialComplexityResult(
                recurrence_equation=recurrence_eq,
                solution=None,
                space_complexity=f"O({total_space})",
                input_space=f"O({input_space})",
                auxiliary_space=f"O({auxiliary_space})",
                recursion_space="O(n)",
                is_recursive=True,
                explanation=f"Estimación: profundidad de pila O(n), espacio total O({total_space})"
            )

    def analyze_recursion_depth(
        self,
        recurrence_eq: RecurrenceEquation
    ) -> str:
        """
        Analiza solo la profundidad de pila de recursión.

        Args:
            recurrence_eq: Ecuación S(n)
        
        Returns:
            str: Complejidad de profundidad
        """
        try:
            solution = self.solver.solve(recurrence_eq.equation)
            return solution.complexity
        except Exception as e:
            self.logger.error(f"Error: {e}")
            return "n"

    def get_space_breakdown(
        self,
        result: SpatialComplexityResult
    ) -> dict:
        """
        Obtiene desglose detallado del uso de espacio.

        Args:
            result: Resultado del análisis

        Returns:
            Dict con desglose
        """
        return {
            "total": result.space_complexity,
            "components": {
                "input": {
                    "complexity": result.input_space,
                    "description": "Espacio ocupado por la entrada del algoritmo",
                    "percentage": self._estimate_percentage(
                        result.input_space,
                        result.space_complexity
                    )
                },
                "auxiliary": {
                    "complexity": result.auxiliary_space,
                    "description": "Espacio adicional usado por el algoritmo",
                    "percentage": self._estimate_percentage(
                        result.auxiliary_space,
                        result.space_complexity
                    )
                },
                "recursion": {
                    "complexity": result.recursion_space,
                    "description": "Espacio de la pila de llamadas recursivas",
                    "percentage": self._estimate_percentage(
                        result.recursion_space,
                        result.space_complexity
                    )
                }
            },
            "dominant_component": self._identify_dominant(
                result.input_space,
                result.auxiliary_space,
                result.recursion_space
            )
        }

    def compare_with_temporal(
        self,
        temporal_complexity: str,
        spatial_complexity: str
    ) -> dict:
        """
        Compara complejidad temporal vs espacial.

        Args:
            temporal_complexity: T(n)
            spatial_complexity: S(n)

        Returns:
            Dict con comparación
        """
        # Limpiar notaciones
        t = temporal_complexity.replace("O(", "").replace(")", "")
        s = spatial_complexity.replace("O(", "").replace(")", "")

        # Orden de complejidades
        order = {
            "1": 0,
            "log n": 1,
            "n": 2,
            "n log n": 3,
            "n²": 4,
            "2^n": 5
        }

        t_order = order.get(t, 999)
        s_order = order.get(s, 999)

        if t_order == s_order:
            relation = "igual"
            comment = "El algoritmo usa tanto tiempo como espacio."
        elif t_order > s_order:
            relation = "temporal_mayor"
            comment = "Time-space tradeoff favorable: menos espacio que tiempo."
        else:
            relation = "espacial_mayor"
            comment = "El algoritmo usa más espacio que tiempo."

        return {
            "temporal": temporal_complexity,
            "spatial": spatial_complexity,
            "relation": relation,
            "comment": comment,
            "is_optimal": self._is_space_optimal(s)
        }

    def _combine_spaces(self, *spaces: str) -> str:
        """Combina múltiples espacios (toma el dominante)"""
        order = {
            "1": 0,
            "log n": 1,
            "n": 2,
            "n log n": 3,
            "n²": 4,
            "n³": 5,
            "2^n": 6
        }

        max_order = 0
        dominant = "1"

        for space in spaces:
            clean = space.replace("O(", "").replace(")", "")
            space_order = order.get(clean, 999)
            if space_order > max_order:
                max_order = space_order
                dominant = clean

        return dominant

    def _estimate_percentage(self, component: str, total: str) -> str:
        """Estima porcentaje aproximado de un componente"""
        comp = component.replace("O(", "").replace(")", "")
        tot = total.replace("O(", "").replace(")", "")

        if comp == tot:
            return "~100%"
        elif comp == "1":
            return "O(1/n) → ~0% para n grande"
        else:
            return "< 50%"

    def _identify_dominant(self, *spaces: str) -> str:
        """Identifica el componente dominante"""
        combined = self._combine_spaces(*spaces)

        for space in spaces:
            if combined in space:
                if "input" in locals():
                    return "input_space"
                elif "auxiliary" in locals():
                    return "auxiliary_space"
                else:
                    return "recursion_space"

        return "unknown"

    def _is_space_optimal(self, space: str) -> bool:
        """Verifica si el espacio es óptimo"""
        clean = space.replace("O(", "").replace(")", "")

        # Constante o logarítmico es óptimo
        return clean in ["1", "log n"]

    def _generate_non_recursive_explanation(
        self,
        total: str,
        input_space: str,
        auxiliary: str
    ) -> str:
        """Genera explicación para algoritmo no recursivo"""
        parts = []

        parts.append("Análisis de Complejidad Espacial:")
        parts.append("")
        parts.append("El algoritmo no es recursivo.")
        parts.append("")
        parts.append(f"Espacio de entrada: O({input_space})")
        parts.append(f"Espacio auxiliar: O({auxiliary})")
        parts.append(f"Espacio total: S(n) = O({total})")

        if auxiliary == "1":
            parts.append("")
            parts.append("✓ Algoritmo in-place: usa espacio auxiliar constante.")

        return "\n".join(parts)

    def _generate_recursive_explanation(
        self,
        recurrence_eq: RecurrenceEquation,
        solution: SolutionResult,
        total: str,
        input_space: str,
        auxiliary: str,
        recursion: str
    ) -> str:
        """Genera explicación para algoritmo recursivo"""
        parts = []

        parts.append("Análisis de Complejidad Espacial:")
        parts.append("")
        parts.append(f"Ecuación de recurrencia: {recurrence_eq.equation}")
        parts.append(f"Caso base: {recurrence_eq.base_case}")
        parts.append("")
        parts.append(f"Método usado: {solution.method_used.value}")
        parts.append(f"Profundidad de pila: S(n) = O({recursion})")
        parts.append("")
        parts.append("Desglose del espacio:")
        parts.append(f"  - Entrada: O({input_space})")
        parts.append(f"  - Auxiliar: O({auxiliary})")
        parts.append(f"  - Pila de recursión: O({recursion})")
        parts.append(f"  - Total: S(n) = O({total})")

        return "\n".join(parts)

# Helper function
def analyze_spatial_complexity(
    recurrence_eq: Optional[RecurrenceEquation],
    input_space: str = "n",
    auxiliary_space: str = "1"
) -> SpatialComplexityResult:
    """
    Helper para análisis rápido de S(n).

    Example:
        >>> from app.core.analyzer.recurrence import build_recurrence_equations
        >>> t_n, s_n = build_recurrence_equations(ast)
        >>> result = analyze_spatial_complexity(s_n)
        >>> print(result.space_complexity)
    """
    analyzer = SpatialComplexityAnalyzer()
    return analyzer.analyze_spatial_complexity(
        recurrence_eq,
        input_space,
        auxiliary_space
    )