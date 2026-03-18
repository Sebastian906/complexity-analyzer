"""
Summarizer

Genera resúmenes ejecutivos y recomendaciones de optimización a partir
de los resultados del análisis. Extraído de analysis_orchestrator.py
donde vivían _generate_summary() y _generate_recommendations().

Separado del orchestrator porque la lógica de presentación no es
responsabilidad de quien coordina el pipeline.
"""

from __future__ import annotations

from typing import Optional

from app.schemas.analysis_result import StructureDetectionResult
from app.schemas.complexity import ComplexityAnalysis, ComplexityClass, SpaceComplexityAnalysis
from app.schemas.pattern import PatternDetectionResult

class Summarizer:
    """
    Genera texto de resumen y listas de recomendaciones.

    Todos los métodos son estáticos — no necesita estado ni
    dependencias externas. Si en el futuro se quiere delegar
    la generación de resúmenes a un LLM, este es el único
    lugar que cambia.
    """

    @staticmethod
    def generate_summary(
        algorithm_name: str,
        complexity: Optional[ComplexityAnalysis],
        space_complexity: Optional[SpaceComplexityAnalysis],
        patterns: Optional[PatternDetectionResult],
        structures: Optional[StructureDetectionResult],
    ) -> str:
        """
        Genera un resumen ejecutivo legible del análisis completo.

        Reemplaza _generate_summary() en analysis_orchestrator.py.

        Args:
            algorithm_name:   Nombre del algoritmo analizado.
            complexity:       Resultado de complejidad temporal (puede ser None
                              si el análisis falló parcialmente).
            space_complexity: Resultado de complejidad espacial.
            patterns:         Resultado de detección de patrones.
            structures:       Resultado de detección de estructuras.

        Returns:
            String multilínea con el resumen ejecutivo.
        """
        lines: list[str] = [f"Algoritmo: {algorithm_name}", ""]

        if complexity:
            lines.append(f"Complejidad temporal: {complexity.big_o}")
            if complexity.theta:
                lines.append(f"Cota ajustada: {complexity.theta}")
        else:
            lines.append("Complejidad temporal: no disponible")

        if space_complexity:
            lines.append(f"Complejidad espacial: {space_complexity.total}")

        if patterns and patterns.primary_pattern:
            primary = patterns.primary_pattern
            lines.append(
                f"Patrón: {primary.pattern.pattern_name} "
                f"({primary.final_score:.0%})"
            )

        if structures and structures.primary_structure:
            primary_s = structures.primary_structure
            lines.append(
                f"Estructura: {primary_s.structure_name} "
                f"({primary_s.confidence:.0%})"
            )

        return "\n".join(lines)

    @staticmethod
    def generate_recommendations(
        complexity: Optional[ComplexityAnalysis],
        patterns: Optional[PatternDetectionResult],
    ) -> list[str]:
        """
        Genera recomendaciones de optimización basadas en el análisis.

        Reemplaza _generate_recommendations() en analysis_orchestrator.py.

        Las recomendaciones son heurísticas estáticas. En el futuro este
        método puede delegar en un LLM para recomendaciones más contextuales
        (ese cambio ocurre aquí, no en el orchestrator).

        Args:
            complexity: Resultado de complejidad temporal.
            patterns:   Resultado de detección de patrones.

        Returns:
            Lista de strings con recomendaciones, posiblemente vacía.
        """
        recommendations: list[str] = []

        if complexity:
            if complexity.big_o_class in (
                ComplexityClass.EXPONENTIAL,
                ComplexityClass.FACTORIAL,
            ):
                recommendations.append(
                    "Complejidad muy alta — considerar memoización o "
                    "programación dinámica para reducirla."
                )
            elif complexity.big_o_class == ComplexityClass.QUADRATIC:
                recommendations.append(
                    "Complejidad cuadrática — evaluar algoritmos alternativos "
                    "como ordenamiento por comparación O(n log n)."
                )
            elif complexity.big_o_class == ComplexityClass.CUBIC:
                recommendations.append(
                    "Complejidad cúbica — revisar si es posible reducir un "
                    "nivel de anidación con precálculo o índices."
                )

        if patterns and patterns.primary_pattern:
            pattern_name = patterns.primary_pattern.pattern.pattern_name.lower()
            final_score = patterns.primary_pattern.final_score

            if "fuerza bruta" in pattern_name and final_score >= 0.7:
                recommendations.append(
                    "Algoritmo de fuerza bruta detectado — explorar técnicas "
                    "de poda (backtracking) o divide y vencerás."
                )
            elif "programación dinámica" in pattern_name and final_score >= 0.7:
                if complexity and complexity.big_o_class in (
                    ComplexityClass.EXPONENTIAL,
                ):
                    recommendations.append(
                        "Se detectó potencial para memoización — "
                        "la versión iterativa (bottom-up) suele ser más eficiente en espacio."
                    )

        return recommendations