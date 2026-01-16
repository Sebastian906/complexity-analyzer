"""
Pattern Scorer - Sistema de Scoring para Patrones

Asigna scores a los patrones detectados y resuelve conflictos
cuando múltiples patrones son detectados simultáneamente.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from app.core.patterns.base_pattern import PatternMatch, PatternType

@dataclass
class ScoredPattern:
    """Patrón con score ajustado"""
    pattern: PatternMatch
    final_score: float
    rank: int = 0
    is_primary: bool = False
    conflicts: List[str] = None

    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []

class PatternScorer:
    """
    Sistema de scoring para patrones detectados.

    Responsabilidades:
    - Ajustar scores basados en conflictos
    - Rankear patrones por confianza
    - Identificar patrón primario
    - Aplicar penalizaciones por conflictos
    """

    def __init__(self):
        # Pesos configurables
        self.weights = {
            "ast_structure": 0.35,
            "code_keywords": 0.25,
            "complexity_match": 0.20,
            "confidence": 0.20
        }

        # Penalizaciones
        self.penalties = {
            "conflicting_patterns": -0.15,
            "missing_indicators": -0.10
        }

        # Umbrales
        self.thresholds = {
            "high_confidence": 0.80,
            "medium_confidence": 0.60,
            "low_confidence": 0.40
        }

        self.dominant_patterns = {
            PatternType.DIVIDE_AND_CONQUER: [
                PatternType.RECURSIVE,
                PatternType.BACKTRACKING,
            ],
            PatternType.DYNAMIC_PROGRAMMING: [
                PatternType.RECURSIVE,
                PatternType.BRUTE_FORCE,
            ],
            PatternType.GREEDY: [
                PatternType.BRUTE_FORCE,
            ],
            # AGREGAR ESTO:
            PatternType.BACKTRACKING: [
                PatternType.RECURSIVE,  # Backtracking domina sobre recursión genérica
            ],
        }

        # Patrones mutuamente excluyentes
        self.mutually_exclusive = {
            PatternType.BRUTE_FORCE: [PatternType.DYNAMIC_PROGRAMMING, PatternType.GREEDY],
            PatternType.DYNAMIC_PROGRAMMING: [PatternType.BRUTE_FORCE],
            PatternType.GREEDY: [PatternType.BRUTE_FORCE, PatternType.BACKTRACKING]
        }

    def score_patterns(
        self,
        patterns: List[PatternMatch]
    ) -> List[ScoredPattern]:
        """
        Asigna scores finales a los patrones detectados.

        Args:
            patterns: Lista de patrones detectados

        Returns:
            Lista de patrones con scores ajustados y rankeados
        """
        if not patterns:
            return []

        scored = []

        for pattern in patterns:
            # Calcular score base
            base_score = pattern.confidence

            # Aplicar ajustes
            adjusted_score = self._adjust_score(pattern, patterns)

            # Detectar conflictos
            conflicts = self._detect_conflicts(pattern, patterns)

            scored_pattern = ScoredPattern(
                pattern=pattern,
                final_score=adjusted_score,
                conflicts=conflicts
            )
            scored.append(scored_pattern)

        # Rankear por score
        scored = self._rank_patterns(scored)

        # Identificar patrón primario
        if scored:
            scored[0].is_primary = True

        return scored

    def _adjust_score(
        self,
        pattern: PatternMatch,
        all_patterns: List[PatternMatch]
    ) -> float:
        """
        Ajusta el score de un patrón basado en contexto.

        Args:
            pattern: Patrón a ajustar
            all_patterns: Todos los patrones detectados

        Returns:
            Score ajustado (0.0 - 1.0)
        """
        score = pattern.confidence

        # Penalización por indicadores faltantes
        missing_ratio = len(pattern.indicators_missing) / pattern.total_indicators
        if missing_ratio > 0.5:
            score += self.penalties["missing_indicators"]

        # Penalización por conflictos
        has_conflicts = self._has_conflicts(pattern, all_patterns)
        if has_conflicts:
            score += self.penalties["conflicting_patterns"]

        # Bonus por alta confianza
        if pattern.confidence >= self.thresholds["high_confidence"]:
            score *= 1.1  # 10% bonus

        # Normalizar a rango [0, 1]
        score = max(0.0, min(1.0, score))

        return score

    def _detect_conflicts(
        self,
        pattern: PatternMatch,
        all_patterns: List[PatternMatch]
    ) -> List[str]:
        """
        Detecta conflictos con otros patrones.

        Args:
            pattern: Patrón a evaluar
            all_patterns: Todos los patrones

        Returns:
            Lista de nombres de patrones en conflicto
        """
        conflicts = []

        exclusive = self.mutually_exclusive.get(pattern.pattern_type, [])

        for other in all_patterns:
            if other.pattern_type == pattern.pattern_type:
                continue

            # Verificar si son mutuamente excluyentes
            if other.pattern_type in exclusive:
                # Solo es conflicto si ambos tienen confianza razonable
                if other.confidence >= self.thresholds["low_confidence"]:
                    conflicts.append(other.pattern_name)

        return conflicts

    def _has_conflicts(
        self,
        pattern: PatternMatch,
        all_patterns: List[PatternMatch]
    ) -> bool:
        """Verifica si el patrón tiene conflictos"""
        return len(self._detect_conflicts(pattern, all_patterns)) > 0

    def _rank_patterns(
        self,
        scored: List[ScoredPattern]
    ) -> List[ScoredPattern]:
        """
        Rankea patrones por score final.

        Args:
            scored: Lista de patrones con scores

        Returns:
            Lista rankeada (mejor primero)
        """
        # Ordenar por score descendente
        scored.sort(key=lambda x: x.final_score, reverse=True)

        # Asignar ranks
        for i, pattern in enumerate(scored, start=1):
            pattern.rank = i

        return scored

    def get_primary_pattern(
        self,
        scored: List[ScoredPattern]
    ) -> Optional[ScoredPattern]:
        """
        Retorna el patrón primario (mayor score).

        Args:
            scored: Lista de patrones rankeados

        Returns:
            Patrón primario o None
        """
        if not scored:
            return None

        return scored[0]

    def filter_by_confidence(
        self,
        scored: List[ScoredPattern],
        min_confidence: float = 0.5
    ) -> List[ScoredPattern]:
        """
        Filtra patrones por confianza mínima.

        Args:
            scored: Lista de patrones
            min_confidence: Confianza mínima requerida

        Returns:
            Lista filtrada
        """
        return [
            p for p in scored
            if p.final_score >= min_confidence
        ]

    def get_confidence_level_name(self, score: float) -> str:
        """Retorna nombre del nivel de confianza"""
        if score >= self.thresholds["high_confidence"]:
            return "Alta"
        elif score >= self.thresholds["medium_confidence"]:
            return "Media"
        elif score >= self.thresholds["low_confidence"]:
            return "Baja"
        else:
            return "Muy Baja"