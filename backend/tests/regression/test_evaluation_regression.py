"""
Tests de regresión semántica usando EvaluationService.

Estos tests verifican que el sistema produzca la complejidad correcta
para algoritmos canónicos. Si un refactor cambia el Big O de mergeSort
de O(n log n) a O(n²), estos tests fallan antes de que llegue a main.

Diferencia con tests/regression/test_regression.py existente:
    - El existente verifica estabilidad de la API (que no rompa)
    - Este verifica corrección semántica (que el resultado sea correcto)

Para ejecutar solo estos tests:
    pytest tests/regression/test_evaluation_regression.py -m regression -v

Para ejecutar en CI y fallar si accuracy < 70%:
    pytest tests/regression/test_evaluation_regression.py::test_regression_threshold
"""

from __future__ import annotations

import pytest

from app.services.evaluation_service import (
    EvaluationService,
    CANONICAL_CASES,
    REGRESSION_THRESHOLD,
    _get_template_code,
)

@pytest.mark.regression
@pytest.mark.asyncio
async def test_regression_threshold():
    """
    El sistema debe superar el umbral mínimo de accuracy.

    Este test es el "gate" de CI — si falla, el deploy se detiene.
    """
    service = EvaluationService(llm_type="none")
    passed, report = await service.run_regression_check()

    assert passed, (
        f"Regression check FAILED: {report.summary_line()}\n"
        f"Casos fallidos:\n"
        + "\n".join(
            f"  - {r.algorithm_name}: esperado={r.expected_big_o}, "
            f"obtenido={r.obtained_big_o}, error={r.error}"
            for r in report.case_results
            if not r.correct
        )
    )

@pytest.mark.regression
@pytest.mark.asyncio
@pytest.mark.parametrize("name,pattern,expected_big_o", CANONICAL_CASES)
async def test_canonical_case(name: str, pattern: str, expected_big_o: str):
    """
    Cada caso canónico individualmente — más fácil de debuggear.

    Si mergeSort falla, el error apunta exactamente a mergeSort,
    no a un informe agregado.
    """
    from app.services.analysis_orchestrator import AnalysisOrchestrator
    from app.schemas.analysis_request import CompleteAnalysisRequest

    code = _get_template_code(name)
    assert code is not None, f"Template '{name}' no existe en _CANONICAL_TEMPLATES"

    orchestrator = AnalysisOrchestrator()
    result = await orchestrator.analyze_complete(
        CompleteAnalysisRequest(
            code=code,
            analyze_complexity=True,
            analyze_patterns=False,
            analyze_structures=False,
            generate_visualizations=False,
            use_cache=False,
        )
    )

    assert result.success, (
        f"{name}: análisis falló con errores: {result.metadata}"
    )
    assert result.complexity is not None, (
        f"{name}: complexity es None — el analyzer no produjo resultado"
    )
    assert result.complexity.big_o == expected_big_o, (
        f"{name} (patrón={pattern}): "
        f"esperado={expected_big_o}, obtenido={result.complexity.big_o}"
    )

@pytest.mark.regression
@pytest.mark.asyncio
async def test_quick_check_completes_fast():
    """
    El quick check debe completar en menos de 20 segundos.

    Diseñado para verificar que el endpoint /health no tenga timeout.
    """
    import time

    service = EvaluationService(llm_type="none")

    start = time.perf_counter()
    report = await service.run_quick_check()
    elapsed = time.perf_counter() - start

    assert elapsed < 20.0, (
        f"Quick check tardó {elapsed:.1f}s — demasiado para un health check"
    )
    assert report.total_cases == 3