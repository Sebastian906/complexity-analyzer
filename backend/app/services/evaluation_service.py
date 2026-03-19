"""
EvaluationService — Evaluación automática del sistema sobre algoritmos canónicos.

Usa los templates del AlgorithmGenerator como ground truth para medir
la precisión del sistema sin intervención manual.

Tres casos de uso:
    1. Regression detection en CI:
           pytest tests/regression/test_evaluation.py
           Falla si accuracy < REGRESSION_THRESHOLD

    2. LLM benchmarking:
           await EvaluationService.benchmark_llms(["ollama", "claude"])
           Compara precisión de cada LLM sobre el mismo conjunto de casos

    3. Health check semántico:
           GET /api/v1/services/evaluation/quick
           Retorna accuracy sobre 5 casos canónicos en <10s

Diseño:
    - EvaluationService solo orquesta — no reimplementa análisis
    - El orchestrator existente hace el trabajo real
    - Los templates de AlgorithmGenerator son el "ground truth"
    - BenchmarkReport es serializable para almacenar histórico
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Umbral mínimo de accuracy para CI — si cae por debajo, el test falla
REGRESSION_THRESHOLD = 0.70

# Casos canónicos con ground truth conocido
# Formato: (nombre_template, patrón, big_o_esperado)
CANONICAL_CASES: list[tuple[str, str, str]] = [
    ("bubbleSort",   "brute_force",          "O(n^2)"),
    ("mergeSort",    "divide_and_conquer",    "O(n log n)"),
    ("quickSort",    "divide_and_conquer",    "O(n log n)"),
    ("fibonacciDP",  "dynamic_programming",   "O(n)"),
]

@dataclass
class CaseResult:
    """Resultado de evaluar un caso canónico."""
    algorithm_name: str
    pattern:        str
    expected_big_o: str
    obtained_big_o: Optional[str]
    correct:        bool
    error:          Optional[str] = None

@dataclass
class BenchmarkReport:
    """
    Reporte de benchmarking del sistema.

    Serializable a dict para almacenar histórico en MongoDB
    o exportar a JSON para CI.
    """
    llm_used:              str
    system_version:        str
    timestamp:             datetime
    total_cases:           int
    correct_cases:         int
    accuracy:              float
    per_pattern_accuracy:  dict[str, float] = field(default_factory=dict)
    case_results:          list[CaseResult] = field(default_factory=list)
    duration_seconds:      float = 0.0
    regression_passed:     bool = True

    def to_dict(self) -> dict:
        return {
            "llm_used":             self.llm_used,
            "system_version":       self.system_version,
            "timestamp":            self.timestamp.isoformat(),
            "total_cases":          self.total_cases,
            "correct_cases":        self.correct_cases,
            "accuracy":             round(self.accuracy, 4),
            "per_pattern_accuracy": {
                k: round(v, 4) for k, v in self.per_pattern_accuracy.items()
            },
            "duration_seconds":     round(self.duration_seconds, 2),
            "regression_passed":    self.regression_passed,
            "cases": [
                {
                    "algorithm":    r.algorithm_name,
                    "pattern":      r.pattern,
                    "expected":     r.expected_big_o,
                    "obtained":     r.obtained_big_o,
                    "correct":      r.correct,
                    "error":        r.error,
                }
                for r in self.case_results
            ],
        }

    def summary_line(self) -> str:
        status = "PASS" if self.regression_passed else "FAIL"
        return (
            f"[{status}] accuracy={self.accuracy:.0%} "
            f"({self.correct_cases}/{self.total_cases}) "
            f"llm={self.llm_used} "
            f"duration={self.duration_seconds:.1f}s"
        )

class EvaluationService:
    """
    Evalúa la precisión del sistema sobre algoritmos canónicos.

    Diseñado para tres contextos:
        - CI/CD: run_regression_check() falla si accuracy < threshold
        - Health check: run_quick_check() evalúa 3 casos en <10s
        - Benchmarking: run_benchmark() evalúa todos los casos

    Args:
        orchestrator: AnalysisOrchestrator a evaluar.
                      Si es None, crea uno con configuración por defecto.
        llm_type:     Nombre del LLM en uso (para el reporte).
    """

    def __init__(
        self,
        orchestrator=None,
        llm_type: str = "default",
    ) -> None:
        self._orchestrator = orchestrator
        self._llm_type = llm_type

    def _get_orchestrator(self):
        """Lazy init para evitar import circular en el module level."""
        if self._orchestrator is None:
            from app.services.analysis_orchestrator import AnalysisOrchestrator
            self._orchestrator = AnalysisOrchestrator()
        return self._orchestrator

    async def run_benchmark(
        self,
        cases: Optional[list[tuple[str, str, str]]] = None,
        max_concurrent: int = 3,
    ) -> BenchmarkReport:
        """
        Ejecuta evaluación completa sobre todos los casos canónicos.

        Args:
            cases:          Lista de (nombre, patrón, big_o_esperado).
                            Si es None, usa CANONICAL_CASES.
            max_concurrent: Máximo de análisis paralelos.

        Returns:
            BenchmarkReport con accuracy y detalle por caso.
        """
        cases = cases or CANONICAL_CASES
        start = datetime.utcnow()
        start_ts = start.timestamp()

        logger.info(
            f"EvaluationService: iniciando benchmark — "
            f"{len(cases)} casos, llm={self._llm_type}"
        )

        results = await self._run_cases(cases, max_concurrent)

        duration = datetime.utcnow().timestamp() - start_ts
        return self._build_report(results, start, duration)

    async def run_quick_check(self) -> BenchmarkReport:
        """
        Evaluación rápida sobre los primeros 3 casos canónicos.

        Diseñada para el endpoint /health — debe completar en <15s.
        """
        quick_cases = CANONICAL_CASES[:3]
        return await self.run_benchmark(cases=quick_cases, max_concurrent=3)

    async def run_regression_check(
        self,
        threshold: float = REGRESSION_THRESHOLD,
    ) -> tuple[bool, BenchmarkReport]:
        """
        Verifica que el sistema supere el umbral mínimo de accuracy.

        Retorna (passed, report). Usar en tests de regresión:
            passed, report = await service.run_regression_check()
            assert passed, report.summary_line()

        Args:
            threshold: Accuracy mínima requerida (default: 0.70).

        Returns:
            (True si passed, BenchmarkReport completo)
        """
        report = await self.run_benchmark()
        passed = report.accuracy >= threshold
        report.regression_passed = passed

        if passed:
            logger.info(f"Regression check PASSED: {report.summary_line()}")
        else:
            logger.warning(f"Regression check FAILED: {report.summary_line()}")

        return passed, report

    async def compare_llms(
        self,
        llm_types: list[str],
    ) -> dict[str, BenchmarkReport]:
        """
        Compara la accuracy del sistema con diferentes LLMs.

        Args:
            llm_types: Lista de nombres de LLM a comparar.
                       Ejemplo: ["ollama", "claude", "gemini"]

        Returns:
            Dict {llm_name: BenchmarkReport}

        Example:
            reports = await service.compare_llms(["ollama", "claude"])
            for llm, report in reports.items():
                print(f"{llm}: {report.accuracy:.0%}")
        """
        results: dict[str, BenchmarkReport] = {}

        for llm_type in llm_types:
            try:
                from app.infrastructure.llm.llm_factory import LLMFactory
                from app.services.analysis_orchestrator import AnalysisOrchestrator

                # Crear orchestrator con el LLM específico
                # (el orchestrator actual no usa LLMs directamente en el pipeline
                #  base, pero este hook sirve para cuando LLMValidationStep esté activo)
                service = EvaluationService(
                    orchestrator=AnalysisOrchestrator(),
                    llm_type=llm_type,
                )
                report = await service.run_benchmark()
                results[llm_type] = report

                logger.info(
                    f"LLM '{llm_type}': accuracy={report.accuracy:.0%} "
                    f"({report.correct_cases}/{report.total_cases})"
                )

            except Exception as exc:
                logger.error(f"Error evaluando LLM '{llm_type}': {exc}")

        return results

    #  Internos                                                           
    async def _run_cases(
        self,
        cases: list[tuple[str, str, str]],
        max_concurrent: int,
    ) -> list[CaseResult]:
        """Ejecuta los casos con semáforo para limitar concurrencia."""
        from app.schemas.analysis_request import CompleteAnalysisRequest

        semaphore = asyncio.Semaphore(max_concurrent)
        orchestrator = self._get_orchestrator()

        async def _evaluate_one(
            name: str,
            pattern: str,
            expected_big_o: str,
        ) -> CaseResult:
            async with semaphore:
                try:
                    code = _get_template_code(name)
                    if code is None:
                        return CaseResult(
                            algorithm_name=name,
                            pattern=pattern,
                            expected_big_o=expected_big_o,
                            obtained_big_o=None,
                            correct=False,
                            error=f"Template '{name}' no encontrado",
                        )

                    result = await orchestrator.analyze_complete(
                        CompleteAnalysisRequest(
                            code=code,
                            analyze_complexity=True,
                            analyze_patterns=False,
                            analyze_structures=False,
                            generate_visualizations=False,
                            use_cache=False,  # Siempre fresco en evaluación
                        )
                    )

                    obtained = (
                        result.complexity.big_o
                        if result.complexity
                        else None
                    )
                    correct = obtained == expected_big_o

                    return CaseResult(
                        algorithm_name=name,
                        pattern=pattern,
                        expected_big_o=expected_big_o,
                        obtained_big_o=obtained,
                        correct=correct,
                    )

                except Exception as exc:
                    logger.warning(f"Error evaluando '{name}': {exc}")
                    return CaseResult(
                        algorithm_name=name,
                        pattern=pattern,
                        expected_big_o=expected_big_o,
                        obtained_big_o=None,
                        correct=False,
                        error=str(exc),
                    )

        tasks = [
            _evaluate_one(name, pattern, big_o)
            for name, pattern, big_o in cases
        ]
        return list(await asyncio.gather(*tasks))

    def _build_report(
        self,
        results: list[CaseResult],
        started_at: datetime,
        duration: float,
    ) -> BenchmarkReport:
        """Construye el BenchmarkReport desde los resultados individuales."""
        from app.core.config import settings

        correct = sum(1 for r in results if r.correct)
        total = len(results)
        accuracy = correct / total if total > 0 else 0.0

        # Accuracy por patrón
        per_pattern: dict[str, list[bool]] = {}
        for r in results:
            per_pattern.setdefault(r.pattern, []).append(r.correct)

        per_pattern_accuracy = {
            pattern: sum(vals) / len(vals)
            for pattern, vals in per_pattern.items()
        }

        return BenchmarkReport(
            llm_used=self._llm_type,
            system_version=getattr(settings, "APP_VERSION", "1.0.0"),
            timestamp=started_at,
            total_cases=total,
            correct_cases=correct,
            accuracy=accuracy,
            per_pattern_accuracy=per_pattern_accuracy,
            case_results=results,
            duration_seconds=duration,
            regression_passed=accuracy >= REGRESSION_THRESHOLD,
        )

#  Templates canónicos embebidos          
# Los templates están aquí (no en AlgorithmGenerator) para que
# EvaluationService sea autónomo sin depender del dataset_generator.
# AlgorithmGenerator los usa para generar variaciones; estos son
# los casos exactos que se evalúan.
_CANONICAL_TEMPLATES: dict[str, str] = {
    "bubbleSort": """algorithm bubbleSort(A[1..n])
begin
    for i ← 1 to n - 1 do
    begin
        for j ← 1 to n - i do
        begin
            if (A[j] > A[j + 1]) then
            begin
                temp ← A[j]
                A[j] ← A[j + 1]
                A[j + 1] ← temp
            end
        end
    end
end""",

    "mergeSort": """algorithm mergeSort(A[1..n])
begin
    if (n > 1) then
    begin
        mid ← n / 2
        call mergeSort(A[1..mid])
        call mergeSort(A[mid+1..n])
        call merge(A, 1, mid, n)
    end
end""",

    "quickSort": """algorithm quickSort(A[1..n], low, high)
begin
    if (low < high) then
    begin
        pivot ← partition(A, low, high)
        call quickSort(A, low, pivot - 1)
        call quickSort(A, pivot + 1, high)
    end
end""",

    "fibonacciDP": """algorithm fibonacciDP(n)
begin
    dp[0] ← 0
    dp[1] ← 1
    for i ← 2 to n do
    begin
        dp[i] ← dp[i-1] + dp[i-2]
    end
    return dp[n]
end""",
}

def _get_template_code(name: str) -> Optional[str]:
    """Retorna el código del template canónico por nombre."""
    return _CANONICAL_TEMPLATES.get(name)

def get_canonical_cases() -> list[tuple[str, str, str]]:
    """Expone los casos canónicos para uso en tests pytest."""
    return list(CANONICAL_CASES)