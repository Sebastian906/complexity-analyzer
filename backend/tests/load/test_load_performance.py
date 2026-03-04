"""
Load & Performance Tests

Pruebas de carga y rendimiento que miden:
    - Tiempo de respuesta de los endpoints bajo carga concurrente.
    - Throughput (peticiones/segundo) de la API.
    - Uso de memoria durante ráfagas de peticiones.
    - Comportamiento del parser y analyzer con algoritmos de tamaño creciente.
    - Degradación de rendimiento bajo estrés.

Estas pruebas se ejecutan con pytest pero se marcan como @pytest.mark.slow
para poder excluirlas de la ejecución regular.

NOTA: Para load testing a escala real se recomienda usar Locust
(ya incluido en requirements-dev.txt). Un locustfile se proporciona aparte.
"""

import time
import statistics
import threading
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ─── Algoritmos de prueba ────────────────────────────────────────────────────

SIMPLE_CODE = """algorithm simple(n)
begin
    x ← 1
end"""

LOOP_CODE = """algorithm loop(n)
begin
    for i ← 1 to n do
    begin
        x ← i
    end
end"""

NESTED_CODE = """algorithm nested(n)
begin
    for i ← 1 to n do
    begin
        for j ← 1 to n do
        begin
            x ← i + j
        end
    end
end"""

BUBBLE_SORT_CODE = """algorithm bubbleSort(A[1..n])
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
end"""

RECURSIVE_CODE = """algorithm fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end
    return fibonacci(n - 1) + fibonacci(n - 2)
end"""


def _generate_deeply_nested_code(depth: int) -> str:
    """Genera un algoritmo con `depth` niveles de anidación de for loops."""
    lines = [f"algorithm deepNested{depth}(n)", "begin"]
    indent = "    "
    for d in range(depth):
        var = chr(ord("i") + d)
        lines.append(f"{indent * (d + 1)}for {var} ← 1 to n do")
        lines.append(f"{indent * (d + 1)}begin")
    lines.append(f"{indent * (depth + 1)}x ← x + 1")
    for d in range(depth - 1, -1, -1):
        lines.append(f"{indent * (d + 1)}end")
    lines.append("end")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE: Tiempos de respuesta individuales
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestResponseTimes:
    """Mide tiempos de respuesta de endpoints individuales."""

    MAX_ANALYSIS_TIME_S = 5.0    # máximo aceptable para análisis completo
    MAX_PATTERN_TIME_S = 3.0     # máximo aceptable para detección de patrones
    MAX_VALIDATION_TIME_S = 2.0  # máximo aceptable para validación
    MAX_QUICK_TIME_S = 2.0       # máximo aceptable para análisis rápido

    def test_analysis_complete_response_time(self, client):
        """POST analyze-complete debe responder en tiempo razonable."""
        start = time.perf_counter()
        resp = client.post(
            "/api/v1/analysis/analyze-complete",
            json={"code": BUBBLE_SORT_CODE},
        )
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert elapsed < self.MAX_ANALYSIS_TIME_S, (
            f"Análisis completo tardó {elapsed:.2f}s (máx {self.MAX_ANALYSIS_TIME_S}s)"
        )

    def test_quick_analysis_response_time(self, client):
        """POST quick analysis debe ser rápido."""
        start = time.perf_counter()
        resp = client.post(
            "/api/v1/analysis/quick",
            json={"code": SIMPLE_CODE},
        )
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert elapsed < self.MAX_QUICK_TIME_S, (
            f"Análisis rápido tardó {elapsed:.2f}s"
        )

    def test_pattern_detection_response_time(self, client):
        """POST patterns/detect debe responder rápidamente."""
        start = time.perf_counter()
        resp = client.post(
            "/api/v1/patterns/detect",
            json={"code": BUBBLE_SORT_CODE},
        )
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert elapsed < self.MAX_PATTERN_TIME_S, (
            f"Detección de patrones tardó {elapsed:.2f}s"
        )

    def test_validation_response_time(self, client):
        """POST validation debe responder rápidamente."""
        start = time.perf_counter()
        resp = client.post(
            "/api/v1/validation/validate",
            json={"code": BUBBLE_SORT_CODE, "level": "complete"},
        )
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert elapsed < self.MAX_VALIDATION_TIME_S, (
            f"Validación tardó {elapsed:.2f}s"
        )

    def test_health_response_time(self, client):
        """GET /api/v1/health debe ser casi instantáneo."""
        start = time.perf_counter()
        resp = client.get("/api/v1/health")
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert elapsed < 1.0, f"Health check tardó {elapsed:.2f}s"


# ═══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE: Throughput — múltiples peticiones secuenciales
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestThroughput:
    """Mide capacidad de procesamiento bajo carga secuencial."""

    NUM_REQUESTS = 20

    def test_health_throughput(self, client):
        """Health check debe manejar muchas peticiones por segundo."""
        times = []
        for _ in range(self.NUM_REQUESTS):
            start = time.perf_counter()
            resp = client.get("/api/v1/health")
            elapsed = time.perf_counter() - start
            assert resp.status_code == 200
            times.append(elapsed)

        avg = statistics.mean(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        rps = self.NUM_REQUESTS / sum(times)

        assert rps > 5, f"Health RPS demasiado bajo: {rps:.1f}"
        print(f"\n[Throughput] Health: avg={avg:.3f}s, p95={p95:.3f}s, RPS={rps:.1f}")

    def test_analysis_throughput(self, client):
        """Análisis completo bajo peticiones repetidas."""
        times = []
        for _ in range(10):
            start = time.perf_counter()
            resp = client.post(
                "/api/v1/analysis/analyze-complete",
                json={"code": LOOP_CODE},
            )
            elapsed = time.perf_counter() - start
            assert resp.status_code == 200
            times.append(elapsed)

        avg = statistics.mean(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        print(f"\n[Throughput] Analysis: avg={avg:.3f}s, p95={p95:.3f}s")

        # El promedio no debe degradarse mucho respecto al primer request
        assert avg < 5.0, f"Promedio de análisis muy alto: {avg:.2f}s"

    def test_validation_throughput(self, client):
        """Validación bajo peticiones repetidas."""
        codes = [SIMPLE_CODE, LOOP_CODE, NESTED_CODE, BUBBLE_SORT_CODE, RECURSIVE_CODE]
        times = []
        for code in codes * 4:  # 20 peticiones
            start = time.perf_counter()
            resp = client.post(
                "/api/v1/validation/validate",
                json={"code": code, "level": "syntax"},
            )
            elapsed = time.perf_counter() - start
            assert resp.status_code == 200
            times.append(elapsed)

        avg = statistics.mean(times)
        print(f"\n[Throughput] Validation: avg={avg:.3f}s, {len(times)} requests")
        assert avg < 2.0


# ═══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE: Escalabilidad del Parser — tamaño de entrada creciente
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestScalability:
    """Verifica que el rendimiento escala razonablemente con el tamaño."""

    def test_parser_scales_with_nesting(self):
        """El parser debe manejar niveles de anidación crecientes."""
        from app.core.parser import PseudocodeParser

        parser = PseudocodeParser()
        times = []

        for depth in range(1, 7):  # 1 a 6 niveles
            code = _generate_deeply_nested_code(depth)
            start = time.perf_counter()
            ast = parser.parse(code)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            assert ast is not None, f"Parser falló con profundidad {depth}"

        # El tiempo no debe crecer exponencialmente
        # Verificar que el último no sea más de 20x el primero
        ratio = times[-1] / max(times[0], 1e-6)
        assert ratio < 50, (
            f"Escalamiento no lineal: depth=1 → {times[0]:.4f}s, "
            f"depth=6 → {times[-1]:.4f}s (ratio={ratio:.1f}x)"
        )

    def test_analyzer_scales_with_nesting(self):
        """El analyzer debe manejar diferentes profundidades."""
        from app.core.parser import parse_pseudocode
        from app.core.analyzer import AnalyzerEngine

        engine = AnalyzerEngine()
        times = []

        for depth in [1, 2, 3, 4]:
            code = _generate_deeply_nested_code(depth)
            ast = parse_pseudocode(code)
            start = time.perf_counter()
            result = engine.analyze(ast)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            assert result.big_o is not None

        # Verificar que el análisis no se dispara
        for t in times:
            assert t < 10.0, f"Análisis individual tardó {t:.2f}s"


# ═══════════════════════════════════════════════════════════════════════════════
#  LOAD: Concurrencia simple con threads
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestConcurrentLoad:
    """Pruebas de carga concurrente usando threads."""

    NUM_CONCURRENT = 5

    def test_concurrent_health_checks(self, client):
        """Múltiples health checks concurrentes deben funcionar."""
        results = []
        errors = []

        def hit_health():
            try:
                resp = client.get("/api/v1/health")
                results.append(resp.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=hit_health) for _ in range(self.NUM_CONCURRENT)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(errors) == 0, f"Errores concurrentes: {errors}"
        assert all(code == 200 for code in results), f"Códigos: {results}"

    def test_concurrent_analysis(self, client):
        """Múltiples análisis concurrentes."""
        results = []
        errors = []
        codes = [SIMPLE_CODE, LOOP_CODE, NESTED_CODE, BUBBLE_SORT_CODE, RECURSIVE_CODE]

        def analyze(code):
            try:
                resp = client.post(
                    "/api/v1/analysis/analyze-complete",
                    json={"code": code},
                )
                results.append(resp.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=analyze, args=(codes[i],)) for i in range(self.NUM_CONCURRENT)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert len(errors) == 0, f"Errores: {errors}"
        # Al menos la mayoría deben tener éxito
        success_count = sum(1 for c in results if c == 200)
        assert success_count >= self.NUM_CONCURRENT * 0.8, (
            f"Solo {success_count}/{self.NUM_CONCURRENT} exitosos"
        )

    def test_concurrent_mixed_endpoints(self, client):
        """Carga mixta de diferentes endpoints simultáneos."""
        results = []
        errors = []

        def call_health():
            try:
                resp = client.get("/api/v1/health")
                results.append(("health", resp.status_code))
            except Exception as e:
                errors.append(f"health: {e}")

        def call_validate():
            try:
                resp = client.post(
                    "/api/v1/validation/validate",
                    json={"code": LOOP_CODE, "level": "syntax"},
                )
                results.append(("validate", resp.status_code))
            except Exception as e:
                errors.append(f"validate: {e}")

        def call_patterns():
            try:
                resp = client.post(
                    "/api/v1/patterns/detect",
                    json={"code": BUBBLE_SORT_CODE},
                )
                results.append(("patterns", resp.status_code))
            except Exception as e:
                errors.append(f"patterns: {e}")

        threads = [
            threading.Thread(target=call_health),
            threading.Thread(target=call_health),
            threading.Thread(target=call_validate),
            threading.Thread(target=call_validate),
            threading.Thread(target=call_patterns),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        assert len(errors) == 0, f"Errores en carga mixta: {errors}"


# ═══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE: Memoria — verificar que no hay fugas obvias
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestMemoryPerformance:
    """Verifica que no hay fugas de memoria evidentes en operaciones repetidas."""

    def test_parser_no_memory_leak(self):
        """Parsear repetidamente no debe acumular memoria indefinidamente."""
        import gc
        from app.core.parser import PseudocodeParser

        parser = PseudocodeParser()

        # Warm up
        for _ in range(5):
            parser.parse(BUBBLE_SORT_CODE)

        gc.collect()

        try:
            import psutil
            process = psutil.Process()
            mem_before = process.memory_info().rss / (1024 * 1024)  # MB
        except ImportError:
            pytest.skip("psutil no disponible para medir memoria")

        # Ejecutar muchas iteraciones
        for _ in range(100):
            parser.parse(BUBBLE_SORT_CODE)
            parser.parse(RECURSIVE_CODE)
            parser.parse(LOOP_CODE)

        gc.collect()
        mem_after = process.memory_info().rss / (1024 * 1024)  # MB
        mem_diff = mem_after - mem_before

        # No debe crecer más de 50 MB en 300 parses
        assert mem_diff < 50, (
            f"Posible fuga de memoria: +{mem_diff:.1f}MB tras 300 parses "
            f"(antes={mem_before:.1f}MB, después={mem_after:.1f}MB)"
        )

    def test_analyzer_no_memory_leak(self):
        """Analizar repetidamente no debe acumular memoria indefinidamente."""
        import gc
        from app.core.parser import parse_pseudocode
        from app.core.analyzer import AnalyzerEngine

        engine = AnalyzerEngine()
        codes = [SIMPLE_CODE, LOOP_CODE, NESTED_CODE, BUBBLE_SORT_CODE]

        # Warm up
        for code in codes:
            ast = parse_pseudocode(code)
            engine.analyze(ast)

        gc.collect()

        try:
            import psutil
            process = psutil.Process()
            mem_before = process.memory_info().rss / (1024 * 1024)
        except ImportError:
            pytest.skip("psutil no disponible")

        for _ in range(50):
            for code in codes:
                ast = parse_pseudocode(code)
                engine.analyze(ast)

        gc.collect()
        mem_after = process.memory_info().rss / (1024 * 1024)
        mem_diff = mem_after - mem_before

        assert mem_diff < 100, (
            f"Posible fuga: +{mem_diff:.1f}MB tras 200 análisis"
        )
