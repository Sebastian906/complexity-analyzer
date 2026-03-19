"""
Tests unitarios para los componentes de resiliencia del LLM:
    - CircuitBreaker
    - LLMEvaluator  
    - LLMEnsemble   
    - DynamicConfig 

Todos los tests son puros — sin red, sin LLMs reales, sin BD.

Para ejecutar:
    pytest tests/unit/test_llm_resilience.py -m unit -v
"""

from __future__ import annotations

import pytest

# CircuitBreaker
@pytest.mark.unit
class TestCircuitBreaker:
    """Tests unitarios del CircuitBreaker."""

    def _make_breaker(self, threshold=3, recovery=60.0):
        from app.infrastructure.llm.llm_circuit_breaker import CircuitBreaker
        return CircuitBreaker(
            name="test",
            failure_threshold=threshold,
            recovery_timeout=recovery,
        )

    def test_initial_state_is_closed(self):
        cb = self._make_breaker()
        from app.infrastructure.llm.llm_circuit_breaker import CircuitState
        assert cb.state == CircuitState.CLOSED
        assert not cb.is_open

    def test_opens_after_threshold_failures(self):
        cb = self._make_breaker(threshold=3)
        from app.infrastructure.llm.llm_circuit_breaker import CircuitState

        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN
        assert cb.is_open

    def test_success_clears_failures(self):
        cb = self._make_breaker(threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()

        from app.infrastructure.llm.llm_circuit_breaker import CircuitState
        assert cb.state == CircuitState.CLOSED
        assert not cb.is_open

    def test_transitions_to_half_open_after_timeout(self):
        import time
        cb = self._make_breaker(threshold=1, recovery=0.01)

        cb.record_failure()
        time.sleep(0.05)  # Dejar pasar el recovery_timeout

        from app.infrastructure.llm.llm_circuit_breaker import CircuitState
        assert cb.state == CircuitState.HALF_OPEN
        assert not cb.is_open

    def test_half_open_to_closed_on_success(self):
        import time
        cb = self._make_breaker(threshold=1, recovery=0.01)

        cb.record_failure()
        time.sleep(0.05)
        _ = cb.is_open  # Trigger transición a HALF_OPEN

        cb.record_success()

        from app.infrastructure.llm.llm_circuit_breaker import CircuitState
        assert cb.state == CircuitState.CLOSED

    def test_half_open_to_open_on_failure(self):
        import time
        cb = self._make_breaker(threshold=1, recovery=0.01)

        cb.record_failure()
        time.sleep(0.05)
        _ = cb.is_open  # HALF_OPEN

        cb.record_failure()  # Falla de nuevo en HALF_OPEN

        from app.infrastructure.llm.llm_circuit_breaker import CircuitState
        assert cb.state == CircuitState.OPEN

    def test_metrics_reflect_state(self):
        cb = self._make_breaker(threshold=3)
        cb.record_failure()
        cb.record_failure()

        metrics = cb.get_metrics()
        assert metrics.name == "test"
        assert metrics.failure_count == 2

    def test_reset_returns_to_initial_state(self):
        cb = self._make_breaker(threshold=1)
        cb.record_failure()
        assert cb.is_open

        cb.reset()
        from app.infrastructure.llm.llm_circuit_breaker import CircuitState
        assert cb.state == CircuitState.CLOSED

# LLMEvaluator
@pytest.mark.unit
class TestLLMEvaluator:
    """Tests unitarios del LLMEvaluator."""

    def _make_evaluator(self):
        from app.infrastructure.llm.llm_evaluator import LLMEvaluator
        return LLMEvaluator()

    def test_valid_json_with_all_fields_scores_high(self):
        evaluator = self._make_evaluator()
        content = '{"big_o": "O(n^2)", "omega": "Omega(n)", "matches_our_analysis": true, "reasoning": "ok"}'
        result = evaluator.evaluate(
            content,
            required_fields=["big_o", "omega", "matches_our_analysis", "reasoning"],
            latency_ms=100.0,
        )
        assert result.score > 0.7
        assert result.is_valid_json
        assert result.has_required_fields

    def test_invalid_json_scores_low(self):
        evaluator = self._make_evaluator()
        result = evaluator.evaluate(
            "esto no es json",
            required_fields=["big_o"],
            latency_ms=100.0,
        )
        assert result.score < 0.5
        assert not result.is_valid_json

    def test_missing_fields_reduces_score(self):
        evaluator = self._make_evaluator()
        result_complete = evaluator.evaluate(
            '{"big_o": "O(n)", "omega": "Omega(1)"}',
            required_fields=["big_o", "omega"],
            latency_ms=100.0,
        )
        result_missing = evaluator.evaluate(
            '{"big_o": "O(n)"}',
            required_fields=["big_o", "omega"],
            latency_ms=100.0,
        )
        assert result_complete.score > result_missing.score

    def test_high_latency_reduces_score(self):
        evaluator = self._make_evaluator()
        content = '{"big_o": "O(n)"}'
        fast = evaluator.evaluate(content, required_fields=[], latency_ms=100.0)
        slow = evaluator.evaluate(content, required_fields=[], latency_ms=9999.0)
        assert fast.score > slow.score

    def test_score_bounded_between_0_and_1(self):
        evaluator = self._make_evaluator()
        for content in ['{"x": 1}', "not json", '{}']:
            result = evaluator.evaluate(content, required_fields=["big_o"], latency_ms=50.0)
            assert 0.0 <= result.score <= 1.0

    def test_evaluate_best_returns_index_of_best(self):
        evaluator = self._make_evaluator()
        responses = [
            ("llm1", "not json", 100.0),
            ("llm2", '{"big_o": "O(n)", "omega": "Omega(1)"}', 200.0),
        ]
        best_idx, evals = evaluator.evaluate_best(
            responses,
            required_fields=["big_o", "omega"],
        )
        assert best_idx == 1  # llm2 tiene mejor respuesta
        assert len(evals) == 2

    def test_is_acceptable_threshold(self):
        evaluator = self._make_evaluator()
        good = evaluator.evaluate(
            '{"big_o": "O(n^2)", "omega": "Omega(n)", "matches_our_analysis": true, "reasoning": "nested"}',
            required_fields=["big_o", "omega", "matches_our_analysis", "reasoning"],
            latency_ms=200.0,
        )
        assert good.is_acceptable  # score >= 0.6

# DynamicConfig
@pytest.mark.unit
class TestDynamicConfig:
    """Tests unitarios del DynamicConfig."""

    def setup_method(self):
        """Resetear cache antes de cada test."""
        from app.services.dynamic_config import DynamicConfig
        DynamicConfig._cache = {}
        DynamicConfig._last_loaded = 0.0

    def test_returns_default_when_no_source(self, tmp_path, monkeypatch):
        """Retorna defaults hardcodeados si no hay Redis ni archivo."""
        from app.services.dynamic_config import DynamicConfig, _FLAGS_FILE

        # Apuntar a un archivo que no existe
        monkeypatch.setattr("app.services.dynamic_config._FLAGS_FILE", tmp_path / "nonexistent.yaml")

        # Redis no disponible en tests
        val = DynamicConfig.get("primary_llm", "ollama")
        assert val == "ollama"

    def test_get_returns_custom_default(self, tmp_path, monkeypatch):
        """Retorna el default del caller si la clave no existe."""
        from app.services.dynamic_config import DynamicConfig

        monkeypatch.setattr("app.services.dynamic_config._FLAGS_FILE", tmp_path / "nonexistent.yaml")
        val = DynamicConfig.get("clave_inexistente", "mi_default")
        assert val == "mi_default"

    def test_loads_from_yaml_file(self, tmp_path, monkeypatch):
        """Carga configuración desde archivo YAML."""
        import yaml
        from app.services.dynamic_config import DynamicConfig

        flags_file = tmp_path / "runtime_flags.yaml"
        flags_file.write_text(yaml.dump({"primary_llm": "claude", "custom_key": 42}))
        monkeypatch.setattr("app.services.dynamic_config._FLAGS_FILE", flags_file)

        DynamicConfig._last_loaded = 0.0  # Forzar recarga

        assert DynamicConfig.get("primary_llm") == "claude"
        assert DynamicConfig.get("custom_key") == 42

    def test_is_step_enabled_returns_true_by_default(self, tmp_path, monkeypatch):
        """is_step_enabled retorna True para pasos desconocidos (seguro por defecto)."""
        from app.services.dynamic_config import DynamicConfig

        monkeypatch.setattr("app.services.dynamic_config._FLAGS_FILE", tmp_path / "nonexistent.yaml")
        assert DynamicConfig.is_step_enabled("parse") is True
        assert DynamicConfig.is_step_enabled("paso_inexistente") is True

    def test_reload_returns_bool(self, tmp_path, monkeypatch):
        """reload() retorna bool indicando si la carga fue exitosa."""
        from app.services.dynamic_config import DynamicConfig

        monkeypatch.setattr("app.services.dynamic_config._FLAGS_FILE", tmp_path / "nonexistent.yaml")
        result = DynamicConfig.reload()
        assert isinstance(result, bool)