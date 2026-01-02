"""
Configuración Global de Pytest

Fixtures compartidos y configuración para todos los tests.
"""

import pytest
from pathlib import Path
from typing import Generator

from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.parser import PseudocodeParser

# Fixtures de Cliente API

@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    """
    Fixture: Cliente de prueba de FastAPI.

    Scope: session - Se crea una vez por sesión de tests
    """
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """
    Fixture: Cliente de prueba (function scope).

    Scope: function - Se crea nuevo cliente para cada test
    """
    with TestClient(app) as client:
        yield client

# Fixtures del Parser

@pytest.fixture(scope="session")
def parser() -> PseudocodeParser:
    """
    Fixture: Instancia del parser.

    Scope: session - Reutilizar la misma instancia
    """
    return PseudocodeParser()

@pytest.fixture(scope="function")
def parser_instance() -> PseudocodeParser:
    """
    Fixture: Nueva instancia del parser para cada test.

    Scope: function - Crear nueva instancia por test
    """
    return PseudocodeParser()

# Fixtures de Códigos de Ejemplo

@pytest.fixture(scope="session")
def sample_algorithms() -> dict:
    """
    Fixture: Algoritmos de ejemplo para testing.

    Returns:
        dict: Diccionario con códigos de ejemplo
    """
    return {
        "simple": """
algorithm simple()
begin
    x ← 1
end
        """.strip(),

        "with_params": """
algorithm test(a, b, c)
begin
    result ← a + b + c
end
        """.strip(),

        "for_loop": """
algorithm forLoop(n)
begin
    for i ← 1 to n do
    begin
        x ← x + 1
    end
end
        """.strip(),

        "nested_loops": """
algorithm nestedLoops(n)
begin
    for i ← 1 to n do
    begin
        for j ← 1 to n do
        begin
            x ← x + 1
        end
    end
end
        """.strip(),

        "bubble_sort": """
algorithm bubbleSort(A[n])
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
end
        """.strip(),

        "binary_search": """
algorithm binarySearch(A[n], x)
begin
    left ← 1
    right ← n

    while (left <= right) do
    begin
        mid ← (left + right) / 2

        if (A[mid] = x) then
        begin
            return mid
        end

        if (A[mid] < x) then
        begin
            left ← mid + 1
        end
        else
        begin
            right ← mid - 1
        end
    end

    return -1
end
        """.strip(),
        
        "fibonacci": """
algorithm fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end
    
    return fibonacci(n - 1) + fibonacci(n - 2)
end
        """.strip(),
        
        "invalid_syntax": """
algorithm invalid(n
begin
    x ← 1
end
        """.strip(),
        
        "empty": """
algorithm empty()
begin
end
        """.strip(),
    }

@pytest.fixture
def simple_algorithm(sample_algorithms) -> str:
    """Fixture: Algoritmo simple"""
    return sample_algorithms["simple"]

@pytest.fixture
def bubble_sort_algorithm(sample_algorithms) -> str:
    """Fixture: Bubble sort"""
    return sample_algorithms["bubble_sort"]

@pytest.fixture
def binary_search_algorithm(sample_algorithms) -> str:
    """Fixture: Binary search"""
    return sample_algorithms["binary_search"]

# Fixtures de Archivos y Paths

@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """
    Fixture: Directorio de fixtures.

    Returns:
        Path: Ruta al directorio tests/fixtures/
    """
    return Path(__file__).parent / "fixtures"

@pytest.fixture(scope="session")
def sample_algorithms_dir(fixtures_dir) -> Path:
    """
    Fixture: Directorio de algoritmos de ejemplo.

    Returns:
        Path: Ruta a tests/fixtures/sample_algorithms/
    """
    path = fixtures_dir / "sample_algorithms"
    path.mkdir(parents=True, exist_ok=True)
    return path

@pytest.fixture(scope="session")
def expected_results_dir(fixtures_dir) -> Path:
    """
    Fixture: Directorio de resultados esperados.

    Returns:
        Path: Ruta a tests/fixtures/expected_results/
    """
    path = fixtures_dir / "expected_results"
    path.mkdir(parents=True, exist_ok=True)
    return path

# Fixtures de Configuración

@pytest.fixture(scope="session")
def test_settings():
    """
    Fixture: Settings de prueba.

    Returns:
        Settings: Configuración para tests
    """
    # En modo test
    original_env = settings.APP_ENV
    settings.APP_ENV = "testing"
    settings.TEST_MODE = True

    yield settings

    # Restaurar
    settings.APP_ENV = original_env
    settings.TEST_MODE = False

# Fixtures para Mocking (futuro)

@pytest.fixture
def mock_llm_response():
    """
    Fixture: Mock de respuesta LLM (para tests sin gastar créditos).
    
    Returns:
        dict: Respuesta mock
    """
    return {
        "big_o": "O(n²)",
        "omega": "Ω(n²)",
        "theta": "Θ(n²)",
        "matches_our_analysis": True,
        "errors": [],
        "warnings": [],
        "reasoning": "Este es un algoritmo de ordenamiento de burbuja con dos ciclos anidados."
    }

# Hooks de Pytest

def pytest_configure(config):
    """Hook: Configuración inicial de pytest"""
    # Registrar markers custom
    config.addinivalue_line(
        "markers",
        "unit: marca tests unitarios"
    )
    config.addinivalue_line(
        "markers",
        "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers",
        "e2e: marca tests end-to-end"
    )
    config.addinivalue_line(
        "markers",
        "slow: marca tests lentos"
    )
    config.addinivalue_line(
        "markers",
        "llm: marca tests que usan LLMs reales (pueden consumir créditos)"
    )

def pytest_collection_modifyitems(config, items):
    """Hook: Modificar items recolectados antes de ejecutar"""
    # Agregar marker 'unit' a tests en tests/unit/
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

# Utilities para Tests

class Helpers:
    """Clase helper con utilidades para tests"""

    @staticmethod
    def create_temp_algorithm_file(tmp_path: Path, code: str, filename: str = "test.txt") -> Path:
        """
        Crea un archivo temporal con código de algoritmo.

        Args:
            tmp_path: Path temporal de pytest
            code: Código del algoritmo
            filename: Nombre del archivo

        Returns:
            Path: Ruta al archivo creado
        """
        file_path = tmp_path / filename
        file_path.write_text(code, encoding='utf-8')
        return file_path

    @staticmethod
    def assert_ast_structure(ast, expected_name: str, expected_params: int):
        """
        Verifica estructura básica del AST.

        Args:
            ast: AST a verificar
            expected_name: Nombre esperado del algoritmo
            expected_params: Número de parámetros esperado
        """
        assert ast is not None
        assert ast.algorithm is not None
        assert ast.algorithm.name == expected_name
        assert len(ast.algorithm.parameters) == expected_params

@pytest.fixture
def helpers():
    """Fixture: Helper utilities"""
    return Helpers