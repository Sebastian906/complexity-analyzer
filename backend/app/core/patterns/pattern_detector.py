"""
Pattern Detector - Detector Principal de Patrones

Orquesta la detección de todos los patrones algorítmicos
y proporciona una interfaz unificada para el análisis.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.core.parser.ast_nodes import ASTNode
from app.core.patterns.base_pattern import PatternMatch, PatternType, BasePatternDetector
from app.core.patterns.pattern_scorer import PatternScorer, ScoredPattern

# Importar todos los detectores
from app.core.patterns.detectors.brute_force_detector import BruteForceDetector
from app.core.patterns.detectors.recursive_detector import RecursiveDetector
from app.core.patterns.detectors.divide_conquer_detector import DivideConquerDetector
from app.core.patterns.detectors.dynamic_programming_detector import DynamicProgrammingDetector
from app.core.patterns.detectors.greedy_detector import GreedyDetector
from app.core.patterns.detectors.backtracking_detector import BacktrackingDetector
from app.core.patterns.detectors.branch_bound_detector import BranchBoundDetector
from app.core.patterns.detectors.sorting_and_searching import SortingDetector, SearchingDetector
from app.core.patterns.detectors.advanced_patterns import (
    QuantumAlgorithmsDetector,
    BioInspiredDetector,
    ApproximationDetector
)

@dataclass
class PatternDetectionResult:
    """
    Resultado completo de la detección de patrones.

    Contiene todos los patrones detectados, rankeados y con metadata.
    """
    # Patrón primario (mayor confianza)
    primary_pattern: Optional[ScoredPattern]

    # Todos los patrones detectados y rankeados
    all_patterns: List[ScoredPattern]

    # Patrones con confianza >= umbral
    confident_patterns: List[ScoredPattern]

    # Resumen textual
    summary: str

    # Metadata adicional
    metadata: Dict[str, Any]

    @property
    def has_patterns(self) -> bool:
        """Retorna True si se detectó al menos un patrón"""
        return len(self.all_patterns) > 0

    @property
    def pattern_count(self) -> int:
        """Número total de patrones detectados"""
        return len(self.all_patterns)

    @property
    def primary_pattern_name(self) -> Optional[str]:
        """Nombre del patrón primario"""
        return self.primary_pattern.pattern.pattern_name if self.primary_pattern else None

    @property
    def primary_confidence(self) -> float:
        """Confianza del patrón primario"""
        return self.primary_pattern.final_score if self.primary_pattern else 0.0

class PatternDetector:
    """
    Detector principal de patrones algorítmicos.

    Coordina la ejecución de todos los detectores específicos,
    rankea los resultados y proporciona un análisis completo.
    """

    def __init__(self):
        # Inicializar todos los detectores
        self.detectors: List[BasePatternDetector] = [
            BruteForceDetector(),
            RecursiveDetector(),
            DivideConquerDetector(),
            DynamicProgrammingDetector(),
            GreedyDetector(),
            BacktrackingDetector(),
            BranchBoundDetector(),
            SortingDetector(),
            SearchingDetector(),
            QuantumAlgorithmsDetector(),
            BioInspiredDetector(),
            ApproximationDetector(),
        ]

        # Sistema de scoring
        self.scorer = PatternScorer()

        # Umbral mínimo de confianza para reportar
        self.min_confidence = 0.3

    def detect(
        self,
        ast: ASTNode,
        min_confidence: Optional[float] = None
    ) -> PatternDetectionResult:
        """
        Detecta todos los patrones presentes en el algoritmo.

        Args:
            ast: Abstract Syntax Tree del algoritmo
            min_confidence: Umbral mínimo de confianza (opcional)

        Returns:
            PatternDetectionResult con todos los patrones detectados
        """
        if min_confidence is None:
            min_confidence = self.min_confidence

        # Ejecutar todos los detectores
        raw_patterns = self._run_detectors(ast)

        # Aplicar scoring
        scored_patterns = self.scorer.score_patterns(raw_patterns)

        # Filtrar por confianza
        confident_patterns = self.scorer.filter_by_confidence(
            scored_patterns,
            min_confidence
        )

        # Obtener patrón primario
        primary = self.scorer.get_primary_pattern(scored_patterns)

        # Generar resumen
        summary = self._generate_summary(primary, confident_patterns)

        # Metadata con estructuras
        metadata = self._build_metadata(scored_patterns, raw_patterns)

        return PatternDetectionResult(
            primary_pattern=primary,
            all_patterns=scored_patterns,
            confident_patterns=confident_patterns,
            summary=summary,
            metadata=metadata
        )

    def detect_specific(
        self,
        ast: ASTNode,
        pattern_type: PatternType
    ) -> Optional[PatternMatch]:
        """
        Detecta un patrón específico.
        
        Args:
            ast: AST del algoritmo
            pattern_type: Tipo de patrón a detectar

        Returns:
            PatternMatch si se detecta, None en caso contrario
        """
        detector = self._get_detector(pattern_type)
        if not detector:
            return None

        return detector.detect(ast)

    def get_available_patterns(self) -> List[str]:
        """
        Retorna lista de patrones que pueden ser detectados.
        
        Returns:
            Lista de nombres de patrones
        """
        return [detector.pattern_name for detector in self.detectors]

    def _run_detectors(self, ast: ASTNode) -> List[PatternMatch]:
        """
        Ejecuta todos los detectores.
        
        Args:
            ast: AST del algoritmo
        
        Returns:
            Lista de todos los matches detectados
        """
        patterns = []

        # Habilitar debug temporalmente
        from rich.console import Console
        debug_console = Console()
        
        debug_console.print("\n[bold cyan]Ejecutando detectores de patrones:[/bold cyan]")
        debug_console.print("=" * 70)

        for detector in self.detectors:
            try:
                match = detector.detect(ast)
                if match:
                    patterns.append(match)
                    # Debug: mostrar patrón detectado con detalles
                    confidence = match.confidence
                    indicators_found = len(match.indicators_found)
                    total_indicators = match.total_indicators
                    debug_console.print(
                        f"[green]✓[/green] {detector.pattern_name:30s} | "
                        f"Confianza: [green]{confidence:5.1%}[/green] | "
                        f"Indicadores: {indicators_found}/{total_indicators}"
                    )
                else:
                    # Debug: patrones no detectados
                    debug_console.print(
                        f"[dim]✗ {detector.pattern_name:30s} | No detectado[/dim]"
                    )
            except Exception as e:
                # Log error pero continuar
                error_msg = str(e)[:50]
                debug_console.print(
                    f"[yellow]{detector.pattern_name:30s} | ERROR:[/yellow] [red]{error_msg}[/red]"
                )
                # Descomentar para ver traceback completo:
                # import traceback
                # traceback.print_exc()
                continue

        debug_console.print("=" * 70)
        debug_console.print(f"[bold]Total de patrones detectados: {len(patterns)}[/bold]\n")
        
        return patterns

    def _get_detector(
        self,
        pattern_type: PatternType
    ) -> Optional[BasePatternDetector]:
        """Obtiene detector específico por tipo"""
        for detector in self.detectors:
            if detector.pattern_type == pattern_type:
                return detector
        return None

    def _generate_summary(
        self,
        primary: Optional[ScoredPattern],
        confident: List[ScoredPattern]
    ) -> str:
        """
        Genera resumen textual del análisis de patrones.

        Args:
            primary: Patrón primario
            confident: Patrones con confianza suficiente

        Returns:
            Resumen en texto
        """
        if not primary:
            return "No se detectaron patrones algorítmicos con suficiente confianza."

        summary_parts = []

        # Patrón primario
        primary_name = primary.pattern.pattern_name
        primary_conf = primary.final_score
        conf_level = self.scorer.get_confidence_level_name(primary_conf)

        summary_parts.append(
            f"Patrón principal detectado: {primary_name} "
            f"(confianza: {primary_conf:.2%} - {conf_level})"
        )

        # Patrones secundarios
        secondary = [p for p in confident if p != primary]
        if secondary:
            secondary_names = [p.pattern.pattern_name for p in secondary]
            summary_parts.append(
                f"Patrones secundarios: {', '.join(secondary_names)}"
            )

        # Complejidad típica del patrón principal
        if primary.pattern.typical_complexity:
            summary_parts.append(
                f"Complejidad típica: {primary.pattern.typical_complexity}"
            )

        # Reasoning del patrón principal
        if primary.pattern.reasoning:
            summary_parts.append(f"Análisis: {primary.pattern.reasoning}")

        return " | ".join(summary_parts)

    def _build_metadata(
        self, 
        patterns: List[ScoredPattern],
        raw_patterns: List[PatternMatch]
    ) -> Dict[str, Any]:
        """
        Construye metadata del análisis incluyendo estructuras detectadas
        
        Args:
            patterns: Patrones con scoring
            raw_patterns: Patrones originales con metadata
        
        Returns:
            Diccionario con metadata completo
        """
        # Extraer estructuras de los raw_patterns
        structures = []
        for raw_match in raw_patterns:
            if hasattr(raw_match, 'metadata') and isinstance(raw_match.metadata, dict):
                # Buscar estructuras en metadata
                if 'data_structures' in raw_match.metadata:
                    structures.extend(raw_match.metadata['data_structures'])
                if 'structures' in raw_match.metadata:
                    structures.extend(raw_match.metadata['structures'])
        
        return {
            "total_patterns_detected": len(patterns),
            "patterns_by_type": {
                p.pattern.pattern_type.value: p.final_score
                for p in patterns
            },
            "highest_confidence": patterns[0].final_score if patterns else 0.0,
            "detection_complete": True,
            "structures": structures,  # Agregar estructuras a metadata
            "raw_pattern_count": len(raw_patterns)
        }

    def __repr__(self) -> str:
        return f"<PatternDetector(detectors={len(self.detectors)})>"