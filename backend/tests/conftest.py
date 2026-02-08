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

# --- NOTA: MongoDB se inicializa automáticamente via lifespan en main.py ---
# No usar fixture de sesión para MongoDB ya que TestClient maneja el ciclo de vida
# a través del lifespan handler de FastAPI, evitando conflictos de event loops.

# Fixtures de Cliente API
@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    """
    Fixture: Cliente de prueba de FastAPI.

    Scope: session - Se crea una vez por sesión de tests
    """
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    Fixture: Cliente de prueba (session scope).

    Scope: session - Un único cliente para evitar problemas de event loop con MongoDB
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

# Fixtures de Servicios (para tests de integración)
@pytest.fixture
def algorithm_service():
    """Fixture: AlgorithmService para tests de integración (sin MongoDB)"""
    from app.services import AlgorithmService
    return AlgorithmService(use_mongodb=False)

@pytest.fixture
def analysis_orchestrator():
    """Fixture: AnalysisOrchestrator para tests de integración"""
    from app.services import AnalysisOrchestrator
    return AnalysisOrchestrator()

@pytest.fixture
def validation_service():
    """Fixture: ValidationService para tests de integración"""
    from app.services import ValidationService
    return ValidationService()

@pytest.fixture
def export_service():
    """Fixture: ExportService para tests de integración"""
    from app.services import ExportService
    return ExportService()

@pytest.fixture
def cache_service():
    """Fixture: CacheService para tests de integración"""
    from app.services import get_cache_service
    return get_cache_service()

# Fixtures de Códigos de Ejemplo
@pytest.fixture(scope="session")
def sample_algorithms() -> dict:
    """
    Fixture: Algoritmos de ejemplo para testing.

    Returns:
        dict: Diccionario con códigos de ejemplo
    """
    return {
        "simple": """algorithm simple()
begin
    x ← 1
end""",

        "with_params": """algorithm test(a, b, c)
begin
    result ← a + b + c
end""",

        "for_loop": """algorithm forLoop(n)
begin
    for i ← 1 to n do
    begin
        x ← x + 1
    end
end""",

        "nested_loops": """algorithm nestedLoops(n)
begin
    for i ← 1 to n do
    begin
        for j ← 1 to n do
        begin
            x ← x + 1
        end
    end
end""",

        # CORREGIDO: Agregar paréntesis en las condiciones IF
        "bubble_sort": """algorithm bubbleSort(A[1..n])
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

        # CORREGIDO: Paréntesis en IF
        "binary_search": """algorithm binarySearch(A[1..n], x)
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
end""",
        
        # CORREGIDO: Paréntesis en IF
        "fibonacci": """algorithm fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end
    return fibonacci(n - 1) + fibonacci(n - 2)
end""",
        
        # CORREGIDO
        "merge_sort": """algorithm mergeSort(A[1..n])
begin
    if (n > 1) then
    begin
        mid ← n / 2
        call mergeSort(A[1..mid])
        call mergeSort(A[mid+1..n])
        call merge(A, 1, mid, n)
    end
end""",
        
        # CORREGIDO
        "quicksort": """algorithm quicksort(A[1..n], low, high)
begin
    if (low < high) then
    begin
        pivot ← partition(A, low, high)
        call quicksort(A, low, pivot - 1)
        call quicksort(A, pivot + 1, high)
    end
end""",
        
        "linear_search": """algorithm linearSearch(A[1..n], x)
begin
    for i ← 1 to n do
    begin
        if (A[i] = x) then
        begin
            return i
        end
    end
    return -1
end""",
        
        # Código inválido (para tests de error)
        "invalid_syntax": """algorithm invalid(n
begin
    x ← 1
end""",
        
        "semantic_error": """algorithm semanticError(n)
begin
    x ← undeclared_var + 1
end""",
        
        "empty": """algorithm empty()
begin
end""",
    }

# Fixtures individuales para algoritmos específicos
@pytest.fixture
def simple_algorithm(sample_algorithms) -> str:
    """Fixture: Algoritmo simple"""
    return sample_algorithms["simple"]

@pytest.fixture
def bubble_sort_algorithm(sample_algorithms) -> str:
    """Fixture: Bubble sort"""
    return sample_algorithms["bubble_sort"]

@pytest.fixture
def bubble_sort_code(sample_algorithms) -> str:
    """Alias: bubble_sort_code (para compatibilidad con tests de integración)"""
    return sample_algorithms["bubble_sort"]

@pytest.fixture
def binary_search_algorithm(sample_algorithms) -> str:
    """Fixture: Binary search"""
    return sample_algorithms["binary_search"]

@pytest.fixture
def binary_search_code(sample_algorithms) -> str:
    """Alias: binary_search_code (para compatibilidad)"""
    return sample_algorithms["binary_search"]

@pytest.fixture
def fibonacci_code(sample_algorithms) -> str:
    """Fixture: Fibonacci recursivo"""
    return sample_algorithms["fibonacci"]

@pytest.fixture
def merge_sort_code(sample_algorithms) -> str:
    """Fixture: Merge Sort"""
    return sample_algorithms["merge_sort"]

@pytest.fixture
def invalid_code(sample_algorithms) -> str:
    """Fixture: Código con errores sintácticos"""
    return sample_algorithms["invalid_syntax"]

@pytest.fixture
def semantic_error_code(sample_algorithms) -> str:
    """Fixture: Código con errores semánticos"""
    return sample_algorithms["semantic_error"]

# NUEVO: Fixtures de Payloads para API (tests de integración)
@pytest.fixture
def bubble_sort_payload(bubble_sort_code) -> dict:
    """Fixture: Payload de Bubble Sort para API"""
    return {
        "code": bubble_sort_code,
        "name": "Bubble Sort",
        "category": "sorting",
        "tags": ["sorting", "quadratic"]
    }

@pytest.fixture
def fibonacci_payload(fibonacci_code) -> dict:
    """Fixture: Payload de Fibonacci para API"""
    return {
        "code": fibonacci_code,
        "name": "Fibonacci",
        "category": "recursion",
        "tags": ["recursive", "exponential"]
    }

@pytest.fixture
def binary_search_payload(binary_search_code) -> dict:
    """Fixture: Payload de búsqueda binaria para API"""
    return {
        "code": binary_search_code,
        "name": "Binary Search",
        "category": "searching",
        "tags": ["search", "divide-conquer"]
    }

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

# Fixture para directorio temporal de exports
@pytest.fixture
def temp_output_dir(tmp_path) -> Path:
    """
    Fixture: Directorio temporal para exports y archivos de test.
    
    Uses pytest's tmp_path fixture to create isolated temp directories.
    
    Returns:
        Path: Ruta a directorio temporal
    """
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir

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
    
    # Métodos adicionales para tests de integración
    @staticmethod
    def assert_analysis_result_complete(result):
        """
        Verifica que un resultado de análisis completo tenga todos los campos.
        
        Args:
            result: Resultado de análisis completo
        """
        assert result is not None
        assert hasattr(result, 'algorithm_name')
        assert hasattr(result, 'big_o')
        assert result.big_o is not None
        
    @staticmethod
    def assert_export_file_exists(file_path: Path, min_size: int = 10):
        """
        Verifica que un archivo exportado exista y no esté vacío.
        
        Args:
            file_path: Path al archivo
            min_size: Tamaño mínimo en bytes
        """
        assert file_path.exists(), f"File {file_path} does not exist"
        assert file_path.stat().st_size >= min_size, f"File {file_path} is too small"

@pytest.fixture
def helpers():
    """Fixture: Helper utilities"""
    return Helpers