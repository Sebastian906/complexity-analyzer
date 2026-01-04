"""
Temporal Complexity - Wrapper especializado para T(n)

Proporciona una interfaz especializada para trabajar con
ecuaciones de recurrencia de complejidad temporal T(n).
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
class TemporalComplexityResult:
    """Resultado del análisis de complejidad temporal"""
    recurrence_equation: Optional[RecurrenceEquation]
    solution: Optional[SolutionResult]
    big_o: str
    is_recursive: bool
    explanation: str

    def to_dict(self) -> dict:
        """Convierte a diccionario"""
        return {
            "recurrence_equation": {
                "equation": self.recurrence_equation.equation,
                "base_case": self.recurrence_equation.base_case,
                "pattern": self.recurrence_equation.recursion_pattern,
                "work_per_call": self.recurrence_equation.work_per_call
            } if self.recurrence_equation else None,

            "solution": {
                "complexity": self.solution.complexity,
                "method": self.solution.method_used.value,
                "form": self.solution.form_detected.name,
                "steps": self.solution.steps,
                "alternative_methods": [
                    m.value for m in self.solution.alternative_methods
                ]
            } if self.solution else None,

            "big_o": self.big_o,
            "is_recursive": self.is_recursive,
            "explanation": self.explanation
        }


class TemporalComplexityAnalyzer:
    """
    Analizador especializado de complejidad temporal.

    Wrapper que combina RecurrenceBuilder y RecurrenceSolver
    para proporcionar análisis completo de T(n).
    """

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.solver = RecurrenceSolver()

    def analyze_temporal_complexity(
        self,
        recurrence_eq: Optional[RecurrenceEquation],
        fallback_complexity: str = "n"
    ) -> TemporalComplexityResult:
        """
        Analiza la complejidad temporal completa.

        Args:
            recurrence_eq: Ecuación de recurrencia (si es recursivo)
            fallback_complexity: Complejidad por defecto (si no recursivo)

        Returns:
            TemporalComplexityResult: Resultado completo
        """
        self.logger.info("Analizando complejidad temporal")

        # Si no es recursivo
        if not recurrence_eq or not recurrence_eq.is_recursive:
            return TemporalComplexityResult(
                recurrence_equation=None,
                solution=None,
                big_o=f"O({fallback_complexity})",
                is_recursive=False,
                explanation=(
                    f"El algoritmo no es recursivo. "
                    f"Complejidad temporal: O({fallback_complexity})"
                )
            )

        # Resolver ecuación de recurrencia
        try:
            solution = self.solver.solve(recurrence_eq.equation)

            # Normalizar complejidad
            big_o = self._normalize_to_big_o(solution.complexity)

            # Generar explicación
            explanation = self._generate_explanation(recurrence_eq, solution)

            return TemporalComplexityResult(
                recurrence_equation=recurrence_eq,
                solution=solution,
                big_o=big_o,
                is_recursive=True,
                explanation=explanation
            )

        except Exception as e:
            self.logger.error(f"Error resolviendo T(n): {e}")

            # Fallback con estimación
            return TemporalComplexityResult(
                recurrence_equation=recurrence_eq,
                solution=None,
                big_o=f"O({fallback_complexity})",
                is_recursive=True,
                explanation=f"No se pudo resolver la ecuación. Estimación: O({fallback_complexity})"
            )

    def solve_custom_equation(
        self,
        equation: str,
        base_case: Optional[str] = None,
        preferred_method: Optional[SolutionMethod] = None
    ) -> TemporalComplexityResult:
        """
        Resuelve una ecuación T(n) personalizada.

        Args:
            equation: Ecuación en string (ej: "T(n) = 2T(n/2) + n")
            base_case: Caso base
            preferred_method: Método preferido

        Returns:
            TemporalComplexityResult
        """
        self.logger.info(f"Resolviendo ecuación personalizada: {equation}")

        try:
            solution = self.solver.solve(equation, base_case, preferred_method)

            big_o = self._normalize_to_big_o(solution.complexity)

            explanation = (
                f"Ecuación T(n) = {equation}\n"
                f"Método usado: {solution.method_used.value}\n"
                f"Resultado: {big_o}"
            )

            return TemporalComplexityResult(
                recurrence_equation=None,
                solution=solution,
                big_o=big_o,
                is_recursive=True,
                explanation=explanation
            )

        except Exception as e:
            self.logger.error(f"Error: {e}")
            raise

    def compare_methods(
        self,
        equation: str
    ) -> dict:
        """
        Compara resultados de diferentes métodos para una ecuación.

        Args:
            equation: Ecuación a resolver

        Returns:
            Dict con resultados de cada método
        """
        self.logger.info(f"Comparando métodos para: {equation}")

        results = {}

        # Detectar forma
        pattern = self.solver._detect_form(equation)
        if not pattern:
            return {"error": "No se pudo detectar la forma"}

        # Obtener métodos aplicables
        applicable = self.solver._get_applicable_methods(pattern.form)

        # Resolver con cada método
        for method in applicable:
            try:
                solution = self.solver.solve(equation, preferred_method=method)
                results[method.value] = {
                    "complexity": solution.complexity,
                    "steps_count": len(solution.steps),
                    "is_exact": solution.is_exact
                }
            except Exception as e:
                results[method.value] = {"error": str(e)}

        return results

    def _normalize_to_big_o(self, complexity: str) -> str:
        """Normaliza la complejidad a notación Big O"""
        if complexity.startswith("O("):
            return complexity

        if complexity.startswith("Θ("):
            # Theta implica Big O
            return complexity.replace("Θ", "O")

        # Agregar notación O()
        return f"O({complexity})"

    def _generate_explanation(
        self,
        recurrence_eq: RecurrenceEquation,
        solution: SolutionResult
    ) -> str:
        """Genera explicación detallada"""
        parts = []

        parts.append("Análisis de Complejidad Temporal:")
        parts.append("")
        parts.append(f"Ecuación de recurrencia: {recurrence_eq.equation}")
        parts.append(f"Caso base: {recurrence_eq.base_case}")
        parts.append(f"Patrón: {recurrence_eq.recursion_pattern}")
        parts.append("")
        parts.append(f"Forma detectada: {solution.form_detected.name}")
        parts.append(f"Método usado: {solution.method_used.value}")
        parts.append(f"Resultado: T(n) = O({solution.complexity})")

        if solution.alternative_methods:
            parts.append("")
            parts.append("Métodos alternativos disponibles:")
            for method in solution.alternative_methods:
                parts.append(f"  - {method.value}")

        parts.append("")
        parts.append(recurrence_eq.explanation)

        return "\n".join(parts)

    def get_complexity_insights(
        self,
        complexity: str
    ) -> dict:
        """
        Obtiene insights sobre una complejidad.

        Args:
            complexity: Complejidad (ej: "n log n")

        Returns:
            Dict con información útil
        """
        # Remover notación O()
        clean_complexity = complexity.replace("O(", "").replace(")", "")

        # Clasificación
        classifications = {
            "1": {
                "class": "Constante",
                "quality": "Excelente",
                "examples": ["Acceso a array", "Operación aritmética"],
                "scalability": "Perfecto"
            },
            "log n": {
                "class": "Logarítmica",
                "quality": "Muy buena",
                "examples": ["Búsqueda binaria", "Operaciones en montículos"],
                "scalability": "Excelente"
            },
            "n": {
                "class": "Lineal",
                "quality": "Buena",
                "examples": ["Búsqueda lineal", "Recorrer array"],
                "scalability": "Bueno"
            },
            "n log n": {
                "class": "Linealítmica",
                "quality": "Aceptable",
                "examples": ["Merge Sort", "Quick Sort (promedio)"],
                "scalability": "Aceptable"
            },
            "n²": {
                "class": "Cuadrática",
                "quality": "Pobre",
                "examples": ["Bubble Sort", "Selection Sort"],
                "scalability": "Pobre para n grande"
            },
            "2^n": {
                "class": "Exponencial",
                "quality": "Muy pobre",
                "examples": ["Fibonacci recursivo", "Subconjuntos"],
                "scalability": "Inviable para n > 30"
            }
        }

        return classifications.get(
            clean_complexity,
            {
                "class": "Desconocida",
                "quality": "Variable",
                "examples": [],
                "scalability": "Depende del contexto"
            }
        )

# Helper function
def analyze_temporal_complexity(
    recurrence_eq: Optional[RecurrenceEquation],
    fallback: str = "n"
) -> TemporalComplexityResult:
    """
    Helper para análisis rápido de T(n).

    Example:
        >>> from app.core.analyzer.recurrence import build_recurrence_equations
        >>> t_n, s_n = build_recurrence_equations(ast)
        >>> result = analyze_temporal_complexity(t_n)
        >>> print(result.big_o)
    """
    analyzer = TemporalComplexityAnalyzer()
    return analyzer.analyze_temporal_complexity(recurrence_eq, fallback)