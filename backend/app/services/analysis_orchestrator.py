"""
Analysis Orchestrator - Orquestación de Análisis Completo

Coordina todos los módulos de análisis (Parser, Analyzer, Patterns, Structures, Visualization)
para proporcionar un análisis completo de algoritmos en un solo flujo.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from app.core.parser import PseudocodeParser, parse_pseudocode, ProgramNode
from app.core.analyzer import AnalyzerEngine
from app.core.patterns import PatternDetector
from app.core.data_structures import StructureIdentifier
from app.core.visualization import (
    generate_recursion_tree,
    generate_execution_flow,
    render_diagram,
    RenderFormat,
)
from app.core.exceptions import (
    ParserException,
    AnalyzerException,
    TimeoutException,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Enums
class AnalysisStatus(str, Enum):
    """Estados de un análisis"""
    PENDING = "pending"
    PARSING = "parsing"
    ANALYZING_COMPLEXITY = "analyzing_complexity"
    DETECTING_PATTERNS = "detecting_patterns"
    DETECTING_STRUCTURES = "detecting_structures"
    GENERATING_VISUALIZATIONS = "generating_visualizations"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisStep(str, Enum):
    """Pasos del análisis"""
    PARSE = "parse"
    COMPLEXITY = "complexity"
    PATTERNS = "patterns"
    STRUCTURES = "structures"
    VISUALIZATION = "visualization"

# DTOs
@dataclass
class CompleteAnalysisRequest:
    """Request para análisis completo"""
    code: str

    # Opciones de análisis
    analyze_complexity: bool = True
    analyze_patterns: bool = True
    analyze_structures: bool = True
    generate_visualizations: bool = True

    # Opciones de complejidad
    analyze_line_by_line: bool = True
    analyze_space: bool = True
    analyze_recurrence: bool = True
    analyze_tight_bounds: bool = True

    # Opciones de patrones
    min_pattern_confidence: float = 0.3
    detect_specific_pattern: Optional[str] = None

    # Opciones de estructuras
    min_structure_confidence: float = 0.3
    analyze_structure_usage: bool = True

    # Opciones de visualización
    generate_recursion_tree: bool = True
    generate_execution_flow: bool = True
    recursion_tree_depth: int = 10
    recursion_tree_start_value: Optional[int] = None
    visualization_format: str = "json"

    # Opciones generales
    timeout: Optional[int] = None
    algorithm_id: Optional[str] = None

@dataclass
class StepResult:
    """Resultado de un paso del análisis"""
    step: AnalysisStep
    status: AnalysisStatus
    duration: float
    success: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@dataclass
class CompleteAnalysisResult:
    """Resultado del análisis completo"""
    # Metadata
    request_id: str
    algorithm_name: str
    status: AnalysisStatus
    started_at: datetime
    completed_at: datetime
    total_duration: float

    # AST
    ast: Optional[ProgramNode] = None

    # Resultados por módulo
    complexity_result: Optional[Dict[str, Any]] = None
    patterns_result: Optional[Dict[str, Any]] = None
    structures_result: Optional[Dict[str, Any]] = None
    visualizations_result: Optional[Dict[str, Any]] = None

    # Steps ejecutados
    steps: List[StepResult] = field(default_factory=list)

    # Resumen ejecutivo
    summary: Optional[str] = None

    # Metadata adicional
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Errores
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Indica si el análisis fue exitoso"""
        return self.status == AnalysisStatus.COMPLETED

    @property
    def failed_steps(self) -> List[StepResult]:
        """Retorna pasos que fallaron"""
        return [s for s in self.steps if not s.success]

    @property
    def successful_steps(self) -> List[StepResult]:
        """Retorna pasos exitosos"""
        return [s for s in self.steps if s.success]

# Orchestrator
class AnalysisOrchestrator:
    """
    Orquestador de análisis completo.

    Coordina todos los módulos para proporcionar un análisis
    integral de algoritmos en pseudocódigo.

    Example:
        >>> orchestrator = AnalysisOrchestrator()
        >>> request = CompleteAnalysisRequest(
        ...     code="algorithm test(n)\\nbegin\\n  for i <- 1 to n do\\n    x <- x + 1\\nend",
        ...     analyze_complexity=True,
        ...     analyze_patterns=True
        ... )
        >>> result = await orchestrator.analyze_complete(request)
        >>> print(result.summary)
    """

    def __init__(
        self,
        parser: Optional[PseudocodeParser] = None,
        analyzer_engine: Optional[AnalyzerEngine] = None,
        pattern_detector: Optional[PatternDetector] = None,
        structure_identifier: Optional[StructureIdentifier] = None,
    ):
        """
        Inicializa el orquestador.

        Args:
            parser: Parser personalizado
            analyzer_engine: Engine de análisis personalizado
            pattern_detector: Detector de patrones personalizado
            structure_identifier: Identificador de estructuras personalizado
        """
        self.parser = parser or PseudocodeParser()
        self.analyzer_engine = analyzer_engine or AnalyzerEngine()
        self.pattern_detector = pattern_detector or PatternDetector()
        self.structure_identifier = structure_identifier or StructureIdentifier()

        logger.info("AnalysisOrchestrator inicializado")

    async def analyze_complete(
        self,
        request: CompleteAnalysisRequest
    ) -> CompleteAnalysisResult:
        """
        Ejecuta análisis completo de un algoritmo.

        Args:
            request: Configuración del análisis

        Returns:
            CompleteAnalysisResult: Resultado completo
        """
        import uuid
        request_id = str(uuid.uuid4())

        logger.info(f"Iniciando análisis completo: {request_id}")

        started_at = datetime.utcnow()
        start_time = time.time()

        result = CompleteAnalysisResult(
            request_id=request_id,
            algorithm_name="",
            status=AnalysisStatus.PENDING,
            started_at=started_at,
            completed_at=started_at,
            total_duration=0.0
        )

        try:
            # Paso 1: Parsing
            ast = await self._step_parse(request, result)
            if not ast:
                result.status = AnalysisStatus.FAILED
                return result

            result.ast = ast
            result.algorithm_name = ast.algorithm.name if ast.algorithm else "unknown"

            # Paso 2: Análisis de Complejidad
            if request.analyze_complexity:
                await self._step_complexity(request, result, ast)

            # Paso 3: Detección de Patrones
            if request.analyze_patterns:
                await self._step_patterns(request, result, ast)

            # Paso 4: Detección de Estructuras
            if request.analyze_structures:
                await self._step_structures(request, result, ast)

            # Paso 5: Generación de Visualizaciones
            if request.generate_visualizations:
                await self._step_visualizations(request, result, ast)

            # Generar resumen
            result.summary = self._generate_summary(result)

            # Marcar como completado
            result.status = AnalysisStatus.COMPLETED

        except TimeoutException as e:
            logger.error(f"Timeout en análisis: {e}")
            result.status = AnalysisStatus.FAILED
            result.errors.append(f"Timeout: {e}")

        except Exception as e:
            logger.error(f"Error en análisis completo: {e}", exc_info=True)
            result.status = AnalysisStatus.FAILED
            result.errors.append(f"Error inesperado: {e}")

        finally:
            # Calcular duración total
            result.completed_at = datetime.utcnow()
            result.total_duration = time.time() - start_time

            # Metadata adicional
            result.metadata = {
                "total_steps": len(result.steps),
                "successful_steps": len(result.successful_steps),
                "failed_steps": len(result.failed_steps),
                "avg_step_duration": (
                    sum(s.duration for s in result.steps) / len(result.steps)
                    if result.steps else 0
                ),
            }

            logger.info(
                f"Análisis completo finalizado: {request_id} - "
                f"Status: {result.status} - Duration: {result.total_duration:.2f}s"
            )

        return result

    # Step Methods
    async def _step_parse(
        self,
        request: CompleteAnalysisRequest,
        result: CompleteAnalysisResult
    ) -> Optional[ProgramNode]:
        """Paso: Parsing"""
        step_start = time.time()
        result.status = AnalysisStatus.PARSING

        logger.info("Ejecutando paso: PARSE")

        try:
            ast = self.parser.parse(request.code, validate=True)

            step = StepResult(
                step=AnalysisStep.PARSE,
                status=AnalysisStatus.COMPLETED,
                duration=time.time() - step_start,
                success=True,
                data={
                    "algorithm_name": ast.algorithm.name if ast.algorithm else None,
                    "parameters_count": len(ast.algorithm.parameters) if ast.algorithm else 0,
                }
            )
            result.steps.append(step)

            return ast

        except ParserException as e:
            logger.error(f"Error en parsing: {e}")
            step = StepResult(
                step=AnalysisStep.PARSE,
                status=AnalysisStatus.FAILED,
                duration=time.time() - step_start,
                success=False,
                error=str(e)
            )
            result.steps.append(step)
            result.errors.append(f"Error de parsing: {e}")
            return None

    async def _step_complexity(
        self,
        request: CompleteAnalysisRequest,
        result: CompleteAnalysisResult,
        ast: ProgramNode
    ) -> None:
        """Paso: Análisis de Complejidad"""
        step_start = time.time()
        result.status = AnalysisStatus.ANALYZING_COMPLEXITY

        logger.info("Ejecutando paso: COMPLEXITY")

        try:
            # Analizar complejidad
            analysis_result = self.analyzer_engine.analyze(
                ast,
                analyze_line_by_line=request.analyze_line_by_line,
                analyze_space=request.analyze_space,
                analyze_recurrence=request.analyze_recurrence,
                analyze_tight_bounds=request.analyze_tight_bounds
            )

            # Convertir a dict
            complexity_data = {
                "big_o": analysis_result.big_o,
                "omega": analysis_result.omega,
                "theta": analysis_result.theta,
                "is_recursive": analysis_result.is_recursive,
                "max_nesting_depth": analysis_result.max_nesting_depth,
            }

            if analysis_result.space_analysis:
                complexity_data["space_complexity"] = {
                    "total": analysis_result.space_analysis.space_complexity,
                    "input": analysis_result.space_analysis.input_space,
                    "auxiliary": analysis_result.space_analysis.auxiliary_space,
                    "recursion": analysis_result.space_analysis.recursion_space,
                }

            if analysis_result.temporal_recurrence and analysis_result.temporal_recurrence.recurrence_equation:
                eq = analysis_result.temporal_recurrence.recurrence_equation
                complexity_data["temporal_recurrence"] = {
                    "equation": eq.equation,
                    "base_case": eq.base_case,
                    "pattern": eq.recursion_pattern,
                }

            if analysis_result.tight_bounds:
                complexity_data["tight_bounds"] = {
                    "has_tight_bound": analysis_result.tight_bounds.has_tight_bound,
                    "theta": analysis_result.tight_bounds.theta,
                }

            result.complexity_result = complexity_data

            step = StepResult(
                step=AnalysisStep.COMPLEXITY,
                status=AnalysisStatus.COMPLETED,
                duration=time.time() - step_start,
                success=True,
                data=complexity_data
            )
            result.steps.append(step)

        except AnalyzerException as e:
            logger.error(f"Error en análisis de complejidad: {e}")
            step = StepResult(
                step=AnalysisStep.COMPLEXITY,
                status=AnalysisStatus.FAILED,
                duration=time.time() - step_start,
                success=False,
                error=str(e)
            )
            result.steps.append(step)
            result.warnings.append(f"Análisis de complejidad parcial: {e}")

    async def _step_patterns(
        self,
        request: CompleteAnalysisRequest,
        result: CompleteAnalysisResult,
        ast: ProgramNode
    ) -> None:
        """Paso: Detección de Patrones"""
        step_start = time.time()
        result.status = AnalysisStatus.DETECTING_PATTERNS

        logger.info("Ejecutando paso: PATTERNS")

        try:
            # Detectar patrones
            patterns_result = self.pattern_detector.detect(
                ast,
                min_confidence=request.min_pattern_confidence
            )

            # Convertir a dict
            patterns_data = {
                "primary_pattern": (
                    {
                        "type": patterns_result.primary_pattern.pattern.pattern_type.value,
                        "name": patterns_result.primary_pattern.pattern.pattern_name,
                        "confidence": patterns_result.primary_pattern.pattern.confidence,
                        "reasoning": patterns_result.primary_pattern.pattern.reasoning,
                    }
                    if patterns_result.primary_pattern else None
                ),
                "pattern_count": patterns_result.pattern_count,
                "confident_patterns": [
                    {
                        "type": p.pattern.pattern_type.value,
                        "name": p.pattern.pattern_name,
                        "confidence": p.pattern.confidence,
                    }
                    for p in patterns_result.confident_patterns
                ],
            }

            result.patterns_result = patterns_data

            step = StepResult(
                step=AnalysisStep.PATTERNS,
                status=AnalysisStatus.COMPLETED,
                duration=time.time() - step_start,
                success=True,
                data=patterns_data
            )
            result.steps.append(step)

        except Exception as e:
            logger.error(f"Error en detección de patrones: {e}")
            step = StepResult(
                step=AnalysisStep.PATTERNS,
                status=AnalysisStatus.FAILED,
                duration=time.time() - step_start,
                success=False,
                error=str(e)
            )
            result.steps.append(step)
            result.warnings.append(f"Detección de patrones fallida: {e}")

    async def _step_structures(
        self,
        request: CompleteAnalysisRequest,
        result: CompleteAnalysisResult,
        ast: ProgramNode
    ) -> None:
        """Paso: Detección de Estructuras"""
        step_start = time.time()
        result.status = AnalysisStatus.DETECTING_STRUCTURES

        logger.info("Ejecutando paso: STRUCTURES")

        try:
            # Identificar estructuras
            structures_result = self.structure_identifier.identify(
                ast,
                min_confidence=request.min_structure_confidence
            )

            # Convertir a dict
            structures_data = {
                "primary_structure": (
                    {
                        "type": structures_result.primary_structure.structure_type.value,
                        "name": structures_result.primary_structure.structure_name,
                        "confidence": structures_result.primary_structure.confidence,
                        "variables": structures_result.primary_structure.variables,
                    }
                    if structures_result.primary_structure else None
                ),
                "structure_count": structures_result.structure_count,
                "structures_found": [
                    {
                        "type": s.structure_type.value,
                        "name": s.structure_name,
                        "confidence": s.confidence,
                    }
                    for s in structures_result.structures_found
                ],
            }

            result.structures_result = structures_data

            step = StepResult(
                step=AnalysisStep.STRUCTURES,
                status=AnalysisStatus.COMPLETED,
                duration=time.time() - step_start,
                success=True,
                data=structures_data
            )
            result.steps.append(step)

        except Exception as e:
            logger.error(f"Error en detección de estructuras: {e}")
            step = StepResult(
                step=AnalysisStep.STRUCTURES,
                status=AnalysisStatus.FAILED,
                duration=time.time() - step_start,
                success=False,
                error=str(e)
            )
            result.steps.append(step)
            result.warnings.append(f"Detección de estructuras fallida: {e}")

    async def _step_visualizations(
        self,
        request: CompleteAnalysisRequest,
        result: CompleteAnalysisResult,
        ast: ProgramNode
    ) -> None:
        """Paso: Generación de Visualizaciones"""
        step_start = time.time()
        result.status = AnalysisStatus.GENERATING_VISUALIZATIONS

        logger.info("Ejecutando paso: VISUALIZATION")

        visualizations = {}

        try:
            # Árbol de recursión
            if request.generate_recursion_tree and result.complexity_result:
                is_recursive = result.complexity_result.get("is_recursive", False)

                if is_recursive:
                    try:
                        tree_result = generate_recursion_tree(
                            ast,
                            start_value=request.recursion_tree_start_value,
                            max_depth=request.recursion_tree_depth
                        )

                        # Renderizar
                        render_format = RenderFormat(request.visualization_format)
                        rendered = render_diagram(tree_result, format=render_format)

                        visualizations["recursion_tree"] = {
                            "type": tree_result.recursion_type.value,
                            "total_calls": tree_result.total_calls,
                            "max_depth": tree_result.max_depth,
                            "content": rendered.content if isinstance(rendered.content, str) else rendered.content.decode('utf-8'),
                            "format": request.visualization_format,
                        }
                    except Exception as e:
                        logger.warning(f"Error generando árbol de recursión: {e}")
                        result.warnings.append(f"Árbol de recursión: {e}")

            # Flujo de ejecución
            if request.generate_execution_flow:
                try:
                    flow_result = generate_execution_flow(ast)

                    # Renderizar
                    render_format = RenderFormat(request.visualization_format)
                    rendered = render_diagram(flow_result, format=render_format)

                    visualizations["execution_flow"] = {
                        "total_nodes": flow_result.statistics["total_nodes"],
                        "total_edges": flow_result.statistics["total_edges"],
                        "content": rendered.content if isinstance(rendered.content, str) else rendered.content.decode('utf-8'),
                        "format": request.visualization_format,
                    }
                except Exception as e:
                    logger.warning(f"Error generando flujo de ejecución: {e}")
                    result.warnings.append(f"Flujo de ejecución: {e}")

            result.visualizations_result = visualizations

            step = StepResult(
                step=AnalysisStep.VISUALIZATION,
                status=AnalysisStatus.COMPLETED,
                duration=time.time() - step_start,
                success=True,
                data={"generated_count": len(visualizations)}
            )
            result.steps.append(step)

        except Exception as e:
            logger.error(f"Error en generación de visualizaciones: {e}")
            step = StepResult(
                step=AnalysisStep.VISUALIZATION,
                status=AnalysisStatus.FAILED,
                duration=time.time() - step_start,
                success=False,
                error=str(e)
            )
            result.steps.append(step)
            result.warnings.append(f"Visualizaciones parciales: {e}")

    def _generate_summary(self, result: CompleteAnalysisResult) -> str:
        """Genera resumen ejecutivo del análisis"""
        lines = [
            f"Análisis completo del algoritmo '{result.algorithm_name}'",
            "",
        ]

        # Complejidad
        if result.complexity_result:
            lines.append("COMPLEJIDAD:")
            lines.append(f"  • Temporal: {result.complexity_result['big_o']}")
            if result.complexity_result.get('theta'):
                lines.append(f"  • Cota ajustada: {result.complexity_result['theta']}")
            if result.complexity_result.get('space_complexity'):
                lines.append(f"  • Espacial: {result.complexity_result['space_complexity']['total']}")
            lines.append("")

        # Patrones
        if result.patterns_result and result.patterns_result.get('primary_pattern'):
            primary = result.patterns_result['primary_pattern']
            lines.append("PATRÓN DETECTADO:")
            lines.append(f"  • {primary['name']} (confianza: {primary['confidence']:.2%})")
            lines.append("")

        # Estructuras
        if result.structures_result and result.structures_result.get('primary_structure'):
            primary = result.structures_result['primary_structure']
            lines.append("ESTRUCTURA DE DATOS:")
            lines.append(f"  • {primary['name']} (confianza: {primary['confidence']:.2%})")
            lines.append("")

        # Estadísticas
        lines.append("ESTADÍSTICAS:")
        lines.append(f"  • Duración: {result.total_duration:.2f}s")
        lines.append(f"  • Pasos completados: {len(result.successful_steps)}/{len(result.steps)}")

        if result.warnings:
            lines.append(f"  • Advertencias: {len(result.warnings)}")

        return "\n".join(lines)