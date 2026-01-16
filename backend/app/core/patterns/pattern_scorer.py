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
    Sistema de scoring mejorado para patrones detectados.
    
    MEJORAS:
    - Penalizaciones más agresivas para conflictos
    - Detección de patrones dominantes
    - Reglas de exclusión mutua más estrictas
    """

    def __init__(self):
        # Pesos configurables
        self.weights = {
            "ast_structure": 0.35,
            "code_keywords": 0.25,
            "complexity_match": 0.20,
            "confidence": 0.20
        }

        # Penalizaciones INCREMENTADAS
        self.penalties = {
            "conflicting_patterns": -0.40,  # Era -0.15, ahora -40%
            "missing_critical_indicators": -0.50,  # NUEVO: -50% si faltan indicadores críticos
            "missing_indicators": -0.15,  # Era -0.10
        }

        # Boost para patrones con alta certeza
        self.boosts = {
            "high_confidence": 1.20,  # +20% si confidence >= 0.80
            "very_high_confidence": 1.35,  # +35% si confidence >= 0.90
            "critical_indicators_found": 1.25,  # +25% si tiene todos los indicadores críticos
        }

        # Umbrales
        self.thresholds = {
            "high_confidence": 0.80,
            "medium_confidence": 0.60,
            "low_confidence": 0.40
        }

        # Patrones mutuamente excluyentes - AMPLIADO
        self.mutually_exclusive = {
            PatternType.BRUTE_FORCE: [
                PatternType.DYNAMIC_PROGRAMMING, 
                PatternType.GREEDY,
                PatternType.DIVIDE_AND_CONQUER,  # NUEVO
            ],
            PatternType.DYNAMIC_PROGRAMMING: [
                PatternType.BRUTE_FORCE,
                PatternType.BACKTRACKING,  # NUEVO
            ],
            PatternType.GREEDY: [
                PatternType.BRUTE_FORCE, 
                PatternType.BACKTRACKING,
                PatternType.DYNAMIC_PROGRAMMING,  # NUEVO
            ],
            PatternType.DIVIDE_AND_CONQUER: [
                PatternType.BACKTRACKING,  # NUEVO - CRÍTICO
                PatternType.BRUTE_FORCE,
                PatternType.DYNAMIC_PROGRAMMING,
            ],
            PatternType.BACKTRACKING: [
                PatternType.DIVIDE_AND_CONQUER,  # NUEVO - CRÍTICO
                PatternType.GREEDY,
                PatternType.DYNAMIC_PROGRAMMING,
            ],
            PatternType.BRANCH_AND_BOUND: [
                PatternType.DIVIDE_AND_CONQUER,  # NUEVO
                PatternType.GREEDY,
            ],
        }

        # Patrones dominantes (tienen prioridad sobre otros)
        self.dominant_patterns = {
            PatternType.DIVIDE_AND_CONQUER: [
                PatternType.RECURSIVE,  # D&C domina sobre recursión genérica
                PatternType.BACKTRACKING,  # D&C domina si ambos tienen scores similares
            ],
            PatternType.DYNAMIC_PROGRAMMING: [
                PatternType.RECURSIVE,
                PatternType.BRUTE_FORCE,
            ],
            PatternType.GREEDY: [
                PatternType.BRUTE_FORCE,
            ],
        }

    def score_patterns(
        self,
        patterns: List[PatternMatch]
    ) -> List[ScoredPattern]:
        """
        Asigna scores finales a los patrones detectados con lógica MEJORADA.
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

        # Resolver conflictos de dominancia
        scored = self._resolve_dominance(scored)

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
        """Ajusta el score con lógica MEJORADA"""
        score = pattern.confidence

        # 1. Penalización por indicadores faltantes
        missing_ratio = len(pattern.indicators_missing) / pattern.total_indicators
        
        # Si faltan más del 50% de indicadores
        if missing_ratio > 0.5:
            score += self.penalties["missing_indicators"]
        
        # Si faltan indicadores CRÍTICOS (weight > 4.0)
        critical_missing = [
            ind for ind in pattern.indicators_missing 
            if ind.weight >= 4.0
        ]
        if critical_missing:
            score += self.penalties["missing_critical_indicators"]

        # 2. Penalización por conflictos - MÁS AGRESIVA
        conflicts = self._detect_conflicts(pattern, all_patterns)
        if conflicts:
            # Penalización proporcional al número de conflictos
            conflict_penalty = self.penalties["conflicting_patterns"] * len(conflicts)
            score += conflict_penalty

        # 3. Boost por alta confianza
        if pattern.confidence >= 0.90:
            score *= self.boosts["very_high_confidence"]
        elif pattern.confidence >= self.thresholds["high_confidence"]:
            score *= self.boosts["high_confidence"]

        # 4. Boost por indicadores críticos encontrados
        critical_found = [
            ind for ind in pattern.indicators_found 
            if ind.weight >= 4.0
        ]
        total_critical = len(critical_found) + len(critical_missing)
        
        if total_critical > 0 and len(critical_found) == total_critical:
            # Tiene TODOS los indicadores críticos
            score *= self.boosts["critical_indicators_found"]

        # Normalizar a rango [0, 1]
        score = max(0.0, min(1.0, score))

        return score

    def _detect_conflicts(
        self,
        pattern: PatternMatch,
        all_patterns: List[PatternMatch]
    ) -> List[str]:
        """Detecta conflictos con otros patrones - MEJORADO"""
        conflicts = []

        exclusive = self.mutually_exclusive.get(pattern.pattern_type, [])

        for other in all_patterns:
            if other.pattern_type == pattern.pattern_type:
                continue

            # Verificar si son mutuamente excluyentes
            if other.pattern_type in exclusive:
                # Solo es conflicto si ambos tienen confianza razonable
                # UMBRAL MÁS BAJO para detectar más conflictos
                if other.confidence >= 0.3:  # Era 0.4
                    conflicts.append(other.pattern_name)

        return conflicts

    def _resolve_dominance(
        self,
        scored: List[ScoredPattern]
    ) -> List[ScoredPattern]:
        """
        Resuelve conflictos de dominancia entre patrones.
        
        NUEVO: Si un patrón dominante tiene score similar a un patrón
        que domina, se aumenta el score del dominante.
        """
        for i, scored_pattern in enumerate(scored):
            pattern_type = scored_pattern.pattern.pattern_type
            
            if pattern_type in self.dominant_patterns:
                dominated = self.dominant_patterns[pattern_type]
                
                for other_scored in scored:
                    other_type = other_scored.pattern.pattern_type
                    
                    if other_type in dominated:
                        # Si scores son similares (diferencia < 20%)
                        score_diff = abs(scored_pattern.final_score - other_scored.final_score)
                        
                        if score_diff < 0.20:
                            # Boost al patrón dominante
                            scored[i].final_score = min(
                                scored_pattern.final_score * 1.15,
                                0.95
                            )
                            
                            # Penalizar al patrón dominado
                            other_scored.final_score *= 0.85
        
        return scored

    def _rank_patterns(
        self,
        scored: List[ScoredPattern]
    ) -> List[ScoredPattern]:
        """Rankea patrones por score final"""
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
        """Retorna el patrón primario (mayor score)"""
        if not scored:
            return None

        return scored[0]

    def filter_by_confidence(
        self,
        scored: List[ScoredPattern],
        min_confidence: float = 0.5
    ) -> List[ScoredPattern]:
        """Filtra patrones por confianza mínima"""
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