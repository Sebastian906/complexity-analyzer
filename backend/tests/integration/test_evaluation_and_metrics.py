"""
tests/integration/test_evaluation_and_metrics.py

Tests de integración para:
    - EvaluationService (Paso 3)
    - Endpoint /evaluation/quick (servicios)
    - Métricas Prometheus (Paso 1 DevOps)
    - LLMEnsemble (Paso 3 DevOps)

Estos tests van en tests/integration/ porque verifican la interacción
entre múltiples componentes, no la lógica interna de uno solo.

Para ejecutar:
    pytest tests/integration/test_evaluation_and_metrics.py -m integration -v
"""

from __future__ import annotations

import pytest

from app.services.evaluation_service import (
    EvaluationService,
    CANONICAL_CASES,
    REGRESSION_THRESHOLD,
    _get_template_code,
)

# EvaluationService
@pytest.mark.integration
@pytest.mark.asyncio
class TestEvaluationServiceIntegration:
    """Tests de integración para EvaluationService."""

    async def test_quick_check_returns_valid_report(self):
        """El quick check retorna un reporte con la estructura esperada."""
        service = EvaluationService(llm_type="none")
        report = await service.run_quick_check()

        assert report.total_cases == 3
        assert 0.0 <= report.accuracy <= 1.0
        assert report.duration_seconds > 0
        assert len(report.case_results) == 3
        for case in report.case_results:
            assert case.algorithm_name is not None
            assert case.expected_big_o is not None
            # obtained puede ser None si el análisis falla

    async def test_benchmark_covers_all_canonical_cases(self):
        """El benchmark cubre todos los casos de CANONICAL_CASES."""
        service = EvaluationService(llm_type="none")
        report = await service.run_benchmark()

        assert report.total_cases == len(CANONICAL_CASES)
        case_names = {r.algorithm_name for r in report.case_results}
        expected_names = {name for name, _, _ in CANONICAL_CASES}
        assert case_names == expected_names

    async def test_report_serializable(self):
        """El reporte es serializable a dict (necesario para el endpoint)."""
        service = EvaluationService(llm_type="none")
        report = await service.run_quick_check()

        d = report.to_dict()
        assert "accuracy" in d
        assert "correct_cases" in d
        assert "total_cases" in d
        assert "cases" in d
        assert isinstance(d["cases"], list)

    async def test_canonical_templates_exist(self):
        """Todos los templates canónicos están definidos."""
        for name, _, _ in CANONICAL_CASES:
            code = _get_template_code(name)
            assert code is not None, f"Template '{name}' no definido"
            assert len(code.strip()) > 0

    async def test_regression_check_returns_bool_and_report(self):
        """run_regression_check retorna (bool, BenchmarkReport)."""
        service = EvaluationService(llm_type="none")
        passed, report = await service.run_regression_check()

        assert isinstance(passed, bool)
        assert report is not None
        assert report.regression_passed == passed

# Endpoint /evaluation/quick (vía TestClient)
@pytest.mark.integration
class TestEvaluationEndpoints:
    """Tests del endpoint de evaluación en la API."""

    def test_evaluation_quick_endpoint_exists(self, client):
        """El endpoint /evaluation/quick responde 200."""
        response = client.get("/api/v1/services/evaluation/quick")
        assert response.status_code == 200

    def test_evaluation_quick_returns_accuracy(self, client):
        """El endpoint retorna el campo accuracy."""
        response = client.get("/api/v1/services/evaluation/quick")
        data = response.json()

        assert "accuracy" in data
        assert "total_cases" in data
        assert "cases" in data
        assert 0.0 <= data["accuracy"] <= 1.0

    def test_evaluation_benchmark_endpoint_exists(self, client):
        """El endpoint /evaluation/benchmark responde (puede tardar)."""
        # No pasar `timeout` al TestClient (deprecado); solo verificar existencia
        response = client.get("/api/v1/services/evaluation/benchmark")
        assert response.status_code == 200
        data = response.json()
        assert "report" in data

# Métricas Prometheus
@pytest.mark.integration
class TestPrometheusMetrics:
    """Tests de las métricas Prometheus (sin Prometheus activo)."""

    def test_metrics_module_importable(self):
        """El módulo de métricas se importa sin error."""
        from app.metrics import METRICS
        assert METRICS is not None

    def test_all_metric_objects_exist(self):
        """Todos los objetos de métricas están definidos."""
        from app.metrics import METRICS

        assert METRICS.analysis_total is not None
        assert METRICS.analysis_duration is not None
        assert METRICS.pipeline_step_duration is not None
        assert METRICS.llm_requests_total is not None
        assert METRICS.llm_response_score is not None
        assert METRICS.llm_circuit_breaker_open is not None
        assert METRICS.cache_hits_total is not None
        assert METRICS.cache_misses_total is not None
        assert METRICS.evaluation_accuracy is not None
        assert METRICS.regression_passed is not None

    def test_metrics_can_be_incremented(self):
        """Los contadores se pueden incrementar sin errores."""
        from app.metrics import METRICS

        # No lanzar excepción al registrar métricas
        METRICS.analysis_total.labels(
            status="success",
            algorithm_pattern="brute_force",
        ).inc()

        METRICS.cache_hits_total.labels(cache_type="analysis").inc()
        METRICS.llm_requests_total.labels(llm_name="ollama", status="success").inc()

    def test_pipeline_middleware_importable(self):
        """El middleware de métricas del pipeline se importa sin error."""
        from app.services.pipeline.metrics_middleware import MetricsPipelineMiddleware
        assert MetricsPipelineMiddleware is not None

# LLM Ensemble
@pytest.mark.integration
@pytest.mark.asyncio
class TestLLMEnsemble:
    """Tests del LLM Ensemble con mocks."""

    async def test_ensemble_requires_minimum_two_llms(self):
        """El ensemble lanza ValueError con menos de 2 LLMs."""
        from app.infrastructure.llm.llm_ensemble import LLMEnsemble
        from unittest.mock import MagicMock

        with pytest.raises(ValueError, match="al menos 2"):
            LLMEnsemble(llms=[MagicMock()])

    async def test_best_score_strategy_selects_highest_score(self):
        """BEST_SCORE selecciona la respuesta con mayor score."""
        from unittest.mock import AsyncMock, MagicMock
        from app.infrastructure.llm.llm_ensemble import LLMEnsemble, EnsembleStrategy
        from app.infrastructure.llm.base_llm import LLMResponse

        # LLM 1: respuesta con big_o incorrecto (sin omega)
        llm1 = MagicMock()
        llm1.generate = AsyncMock(return_value=LLMResponse(
            content='{"big_o": "O(n)", "omega": "Omega(1)", "matches_our_analysis": true, "reasoning": "test"}',
            model="mock1", tokens_used=10, finish_reason="stop", metadata={}
        ))

        # LLM 2: respuesta JSON completa y correcta
        llm2 = MagicMock()
        llm2.generate = AsyncMock(return_value=LLMResponse(
            content='{"big_o": "O(n^2)", "omega": "Omega(n)", "matches_our_analysis": false, "reasoning": "two nested loops"}',
            model="mock2", tokens_used=10, finish_reason="stop", metadata={}
        ))

        ensemble = LLMEnsemble(
            llms=[llm1, llm2],
            strategy=EnsembleStrategy.BEST_SCORE,
        )
        result = await ensemble.validate(
            prompt="test",
            required_fields=["big_o", "omega", "matches_our_analysis", "reasoning"],
        )

        assert result.winning_response is not None
        assert "big_o" in result.winning_response
        assert len(result.llms_consulted) == 2

    async def test_majority_vote_strategy_finds_consensus(self):
        """MAJORITY_VOTE encuentra consenso cuando 2/3 LLMs coinciden."""
        from unittest.mock import AsyncMock, MagicMock
        from app.infrastructure.llm.llm_ensemble import LLMEnsemble, EnsembleStrategy
        from app.infrastructure.llm.base_llm import LLMResponse

        response_template = (
            '{{"big_o": "{big_o}", "omega": "Omega(n)", '
            '"matches_our_analysis": true, "reasoning": "test"}}'
        )

        def make_llm(big_o: str):
            llm = MagicMock()
            llm.generate = AsyncMock(return_value=LLMResponse(
                content=response_template.format(big_o=big_o),
                model=f"mock_{big_o}", tokens_used=10,
                finish_reason="stop", metadata={}
            ))
            return llm

        # 2 de 3 votan O(n^2)
        ensemble = LLMEnsemble(
            llms=[make_llm("O(n^2)"), make_llm("O(n^2)"), make_llm("O(n)")],
            strategy=EnsembleStrategy.MAJORITY_VOTE,
            min_agreement=0.6,
        )
        result = await ensemble.validate(
            prompt="test",
            required_fields=["big_o", "omega", "matches_our_analysis"],
        )

        assert result.winning_response["big_o"] == "O(n^2)"
        assert result.agreement_score >= 0.6
        assert result.consensus_reached

    async def test_ensemble_handles_llm_failure_gracefully(self):
        """Si un LLM falla, el ensemble continúa con los demás."""
        from unittest.mock import AsyncMock, MagicMock
        from app.infrastructure.llm.llm_ensemble import LLMEnsemble, EnsembleStrategy
        from app.infrastructure.llm.base_llm import LLMResponse

        # LLM 1 falla
        failing_llm = MagicMock()
        failing_llm.generate = AsyncMock(side_effect=ConnectionError("LLM no disponible"))

        # LLM 2 funciona
        working_llm = MagicMock()
        working_llm.generate = AsyncMock(return_value=LLMResponse(
            content='{"big_o": "O(n^2)", "omega": "Omega(n)", "matches_our_analysis": true, "reasoning": "ok"}',
            model="mock", tokens_used=10, finish_reason="stop", metadata={}
        ))

        ensemble = LLMEnsemble(
            llms=[failing_llm, working_llm],
            strategy=EnsembleStrategy.BEST_SCORE,
        )
        result = await ensemble.validate(
            prompt="test",
            required_fields=["big_o", "omega"],
        )

        assert result.winning_response is not None
        assert len(result.llms_failed) == 1
        assert len(result.llms_consulted) == 1

    async def test_ensemble_raises_when_all_fail(self):
        """RuntimeError si todos los LLMs fallan."""
        from unittest.mock import AsyncMock, MagicMock
        from app.infrastructure.llm.llm_ensemble import LLMEnsemble, EnsembleStrategy

        llm1 = MagicMock()
        llm1.generate = AsyncMock(side_effect=ConnectionError("fallo"))
        llm2 = MagicMock()
        llm2.generate = AsyncMock(side_effect=ConnectionError("fallo"))

        ensemble = LLMEnsemble(
            llms=[llm1, llm2],
            strategy=EnsembleStrategy.BEST_SCORE,
        )

        with pytest.raises(RuntimeError, match="Todos los LLMs del ensemble fallaron"):
            await ensemble.validate(prompt="test", required_fields=[])