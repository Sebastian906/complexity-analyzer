"""
Black Box Tests - Pruebas de Caja Negra

Se prueba la funcionalidad del sistema SIN conocer la implementación interna.
Solo se interactúa a través de la API pública (endpoints HTTP).

Enfoque:
    - Equivalence Partitioning: dividir inputs en clases válidas/inválidas.
    - Boundary Value Analysis: probar valores límite.
    - Decision Table Testing: combinar condiciones de entrada.
    - Error Guessing: buscar errores comunes esperados.

Se verifica solo INPUT → OUTPUT correcto, sin importar cómo se llega al resultado.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ═══════════════════════════════════════════════════════════════════════════════
#  EQUIVALENCE PARTITIONING — Clases de entrada para Análisis
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnalysisEquivalencePartitions:
    """
    Clases de equivalencia para el endpoint de análisis:
        1. Algoritmo simple sin loops (constante)
        2. Algoritmo con un loop (lineal)
        3. Algoritmo con loops anidados (cuadrático)
        4. Algoritmo recursivo simple
        5. Algoritmo recursivo con divide y vencerás
        6. Código vacío (inválido)
        7. Código con sintaxis incorrecta (inválido)
    """

    def test_constant_algorithm(self, client):
        """Clase 1: constante → O(1)"""
        code = """algorithm constant()
begin
    x ← 1
    y ← 2
    z ← x + y
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200
        big_o = resp.json()["complexity"]["big_o"].lower()
        assert "1" in big_o, f"Constante esperado, obtenido: {big_o}"

    def test_linear_algorithm(self, client):
        """Clase 2: un loop → O(n)"""
        code = """algorithm linear(n)
begin
    for i ← 1 to n do
    begin
        x ← i
    end
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200
        big_o = resp.json()["complexity"]["big_o"].lower()
        assert "n" in big_o and "²" not in big_o and "^2" not in big_o

    def test_quadratic_algorithm(self, client):
        """Clase 3: loops anidados → O(n²)"""
        code = """algorithm quadratic(n)
begin
    for i ← 1 to n do
    begin
        for j ← 1 to n do
        begin
            x ← i + j
        end
    end
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200
        big_o = resp.json()["complexity"]["big_o"]
        assert "n²" in big_o or "n^2" in big_o, f"Cuadrático esperado: {big_o}"

    def test_recursive_algorithm(self, client):
        """Clase 4: recursión simple."""
        code = """algorithm factorial(n)
begin
    if (n <= 1) then
    begin
        return 1
    end
    return n * factorial(n - 1)
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["complexity"]["big_o"] is not None

    def test_divide_and_conquer(self, client):
        """Clase 5: divide y vencerás."""
        code = """algorithm mergeSort(A[1..n])
begin
    if (n > 1) then
    begin
        mid ← n / 2
        call mergeSort(A[1..mid])
        call mergeSort(A[mid+1..n])
        call merge(A, 1, mid, n)
    end
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_empty_body_algorithm(self, client):
        """Clase 6: algoritmo con cuerpo vacío."""
        code = """algorithm empty()
begin
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200
        big_o = resp.json()["complexity"]["big_o"].lower()
        assert "1" in big_o

    def test_invalid_syntax_rejected(self, client):
        """Clase 7: sintaxis inválida debe fallar."""
        code = "algorithm broken(\nbegin\n    x ← 1\nend"
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        # Debe retornar error (400 o 500)
        assert resp.status_code in (400, 500)


# ═══════════════════════════════════════════════════════════════════════════════
#  BOUNDARY VALUE ANALYSIS — Valores límite
# ═══════════════════════════════════════════════════════════════════════════════

class TestBoundaryValues:
    """Pruebas de valores límite en entradas."""

    def test_minimal_valid_algorithm(self, client):
        """El algoritmo válido más pequeño posible."""
        code = """algorithm a()
begin
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200

    def test_single_statement(self, client):
        """Algoritmo con una sola sentencia."""
        code = """algorithm one(n)
begin
    x ← 1
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_algorithm_with_many_parameters(self, client):
        """Algoritmo con muchos parámetros."""
        code = """algorithm manyParams(a, b, c, d, e, f, g, h)
begin
    x ← a + b + c + d + e + f + g + h
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200

    def test_zero_confidence_pattern_detection(self, client):
        """Detección de patrones con confianza mínima 0."""
        code = """algorithm simple(n)
begin
    x ← 1
end"""
        resp = client.post(
            "/api/v1/patterns/detect",
            json={"code": code, "options": {"min_confidence": 0.0}},
        )
        assert resp.status_code == 200

    def test_max_confidence_pattern_detection(self, client):
        """Detección con confianza máxima 1.0 — puede no encontrar nada."""
        code = """algorithm simple(n)
begin
    x ← 1
end"""
        resp = client.post(
            "/api/v1/patterns/detect",
            json={"code": code, "options": {"min_confidence": 1.0}},
        )
        assert resp.status_code == 200
        # Con confianza 1.0 es probable que no encuentre patrones
        data = resp.json()
        assert isinstance(data["patterns_found"], list)

    def test_empty_code_validation(self, client):
        """Validar código vacío debe retornar error."""
        resp = client.post(
            "/api/v1/validation/validate",
            json={"code": "", "level": "syntax"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False

    def test_whitespace_only_code(self, client):
        """Código que es solo espacios debe fallar."""
        resp = client.post(
            "/api/v1/validation/validate",
            json={"code": "   \n\n  \t  ", "level": "syntax"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False


# ═══════════════════════════════════════════════════════════════════════════════
#  DECISION TABLE — Combinaciones de opciones de análisis
# ═══════════════════════════════════════════════════════════════════════════════

class TestDecisionTable:
    """Pruebas combinatorias de opciones de análisis."""

    ALGORITHM = """algorithm bubbleSort(A[1..n])
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

    @pytest.mark.parametrize("line_by_line,spatial,recurrence,tight_bounds", [
        (True,  True,  True,  True),   # Todo activo
        (False, False, False, False),  # Todo inactivo
        (True,  False, False, False),  # Solo línea por línea
        (False, True,  False, False),  # Solo espacial
        (False, False, True,  False),  # Solo recurrencia
        (False, False, False, True),   # Solo tight bounds
        (True,  True,  False, False),  # Línea + espacial
    ])
    def test_analysis_option_combinations(
        self, client, line_by_line, spatial, recurrence, tight_bounds
    ):
        """Cada combinación de opciones debe producir un resultado válido."""
        resp = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": self.ALGORITHM,
                "options": {
                    "analyze_line_by_line": line_by_line,
                    "analyze_spatial": spatial,
                    "analyze_recurrence": recurrence,
                    "calculate_tight_bounds": tight_bounds,
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        # Los campos opcionales deben ser None o presentes según las opciones
        assert data["complexity"]["big_o"] is not None

    @pytest.mark.parametrize("level", ["syntax", "semantic", "structural", "complete"])
    def test_validation_levels(self, client, level):
        """Todos los niveles de validación deben funcionar."""
        resp = client.post(
            "/api/v1/validation/validate",
            json={"code": self.ALGORITHM, "level": level},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "is_valid" in data
        assert isinstance(data["is_valid"], bool)

    @pytest.mark.parametrize("format_name", ["json", "markdown", "html", "csv"])
    def test_export_formats(self, client, format_name):
        """Cada formato de exportación debe funcionar."""
        resp = client.post(
            "/api/v1/export/export",
            json={
                "code": self.ALGORITHM,
                "algorithm_name": f"Test {format_name}",
                "options": {
                    "format": format_name,
                    "template": "minimal",
                    "sections": ["algorithm_info"],
                },
            },
        )
        assert resp.status_code in (200, 422), (
            f"Formato {format_name} falló: {resp.status_code}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  ERROR GUESSING — Entradas problemáticas conocidas
# ═══════════════════════════════════════════════════════════════════════════════

class TestErrorGuessing:
    """Pruebas con inputs que podrían causar errores inesperados."""

    def test_unicode_in_code(self, client):
        """Código con caracteres unicode no debe crashear la API."""
        code = """algorithm unicodeTest(n)
begin
    x ← 1
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        # Puede ser 200 o 400, pero nunca 500
        assert resp.status_code != 500

    def test_very_long_variable_names(self, client):
        """Variables con nombres muy largos."""
        long_var = "x" * 200
        code = f"""algorithm longVars(n)
begin
    {long_var} ← 1
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code != 500

    def test_deeply_nested_if_else(self, client):
        """if/else anidados profundamente."""
        code = """algorithm deepIf(n)
begin
    if (n > 1) then
    begin
        if (n > 2) then
        begin
            if (n > 3) then
            begin
                x ← 1
            end
            else
            begin
                x ← 2
            end
        end
    end
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200

    def test_multiple_return_statements(self, client):
        """Algoritmo con múltiples returns."""
        code = """algorithm multiReturn(n)
begin
    if (n > 0) then
    begin
        return 1
    end
    return 0
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200

    def test_json_body_missing_code(self, client):
        """Request sin campo 'code' debe retornar error de validación."""
        resp = client.post(
            "/api/v1/analysis/analyze-complete",
            json={"options": {}},
        )
        assert resp.status_code == 422  # Validation error

    def test_json_body_null_code(self, client):
        """Request con code=null."""
        resp = client.post(
            "/api/v1/analysis/analyze-complete",
            json={"code": None},
        )
        assert resp.status_code == 422

    def test_algorithm_with_array_access(self, client):
        """Algoritmo con acceso a arrays."""
        code = """algorithm arrayAccess(A[1..n])
begin
    for i ← 1 to n do
    begin
        A[i] ← A[i] + 1
    end
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_algorithm_with_while_loop(self, client):
        """Algoritmo con while loop."""
        code = """algorithm whileLoop(n)
begin
    i ← 1
    while (i <= n) do
    begin
        i ← i + 1
    end
end"""
        resp = client.post("/api/v1/analysis/analyze-complete", json={"code": code})
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
#  BLACK BOX: Patrones — comportamiento esperado por tipo
# ═══════════════════════════════════════════════════════════════════════════════

class TestPatternBlackBox:
    """Verifica que la detección de patrones devuelve resultados coherentes."""

    def test_sorting_pattern_detected_for_bubble_sort(self, client):
        """Bubble sort debe ser detectado como sorting o brute force."""
        code = """algorithm bubbleSort(A[1..n])
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
        resp = client.post("/api/v1/patterns/detect", json={"code": code})
        assert resp.status_code == 200
        types = [p["pattern_type"] for p in resp.json()["patterns_found"]]
        assert any(t in ("brute_force", "sorting") for t in types), (
            f"Se esperaba brute_force o sorting, obtenido: {types}"
        )

    def test_recursive_pattern_detected(self, client):
        """Un algoritmo recursivo debe ser detectado como recursive."""
        code = """algorithm factorial(n)
begin
    if (n <= 1) then
    begin
        return 1
    end
    return n * factorial(n - 1)
end"""
        resp = client.post("/api/v1/patterns/detect", json={"code": code})
        assert resp.status_code == 200
        types = [p["pattern_type"] for p in resp.json()["patterns_found"]]
        assert "recursive" in types, f"Se esperaba recursive, obtenido: {types}"

    def test_pattern_count_matches_list(self, client):
        """El campo pattern_count debe coincidir con len(patterns_found)."""
        code = """algorithm test(n)
begin
    for i ← 1 to n do
    begin
        x ← i
    end
end"""
        resp = client.post("/api/v1/patterns/detect", json={"code": code})
        assert resp.status_code == 200
        data = resp.json()
        assert data["pattern_count"] == len(data["patterns_found"])


# ═══════════════════════════════════════════════════════════════════════════════
#  BLACK BOX: Structures — comportamiento esperado
# ═══════════════════════════════════════════════════════════════════════════════

class TestStructureBlackBox:
    """Verifica detección de estructuras como caja negra."""

    def test_array_detected_in_array_algorithm(self, client):
        """Un algoritmo que usa A[i] debe detectar array."""
        code = """algorithm arraySum(A[1..n])
begin
    sum ← 0
    for i ← 1 to n do
    begin
        sum ← sum + A[i]
    end
    return sum
end"""
        resp = client.post("/api/v1/structures/detect", json={"code": code})
        assert resp.status_code == 200
        types = [s["structure_type"] for s in resp.json()["structures_found"]]
        assert any("array" in t.lower() for t in types), (
            f"Se esperaba array, obtenido: {types}"
        )

    def test_no_structures_in_pure_computation(self, client):
        """Algoritmo sin estructuras de datos puede no detectar ninguna."""
        code = """algorithm compute(n)
begin
    x ← n * 2
    y ← x + 1
end"""
        resp = client.post("/api/v1/structures/detect", json={"code": code})
        assert resp.status_code == 200
        # Es válido detectar 0 o más estructuras
        data = resp.json()
        assert isinstance(data["structures_found"], list)
