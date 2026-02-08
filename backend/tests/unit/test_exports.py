"""
Tests para el sistema de exportación

Prueba los exportadores en diferentes formatos.
"""

import pytest
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from app.infrastructure.export import (
    ExportFormat,
    ExporterFactory,
    export_analysis,
    export_to_multiple_formats,
    PDF_AVAILABLE,
    EXCEL_AVAILABLE,
)

# Mock classes para evitar dependencia de Beanie/MongoDB
@dataclass
class MockAlgorithm:
    """Mock de Algorithm para tests sin MongoDB"""
    name: str
    code: str
    language: str = "pseudocode"
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

@dataclass
class MockAnalysisResult:
    """Mock de AnalysisResult para tests sin MongoDB"""
    algorithm: MockAlgorithm
    big_o: str
    omega: str
    theta: Optional[str] = None
    space_complexity: Optional[str] = None
    temporal_recurrence: Optional[str] = None
    spatial_recurrence: Optional[str] = None
    line_by_line: Dict[str, Any] = field(default_factory=dict)
    analysis_time: float = 0.0
    analyzer_version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    algorithm_id: Optional[str] = None

@dataclass
class MockPatternDetection:
    """Mock de PatternDetection para tests sin MongoDB"""
    algorithm: MockAlgorithm
    primary_pattern: str
    primary_confidence: float
    patterns_found: List[Dict[str, Any]] = field(default_factory=list)
    structures_found: List[Dict[str, Any]] = field(default_factory=list)
    detection_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


# FIXTURES
@pytest.fixture
def sample_algorithm():
    """Crea un algoritmo de ejemplo para pruebas"""
    return MockAlgorithm(
        name="quicksort",
        code="""algorithm quicksort(A[1..n])
begin
    if n > 1 then
    begin
        q ← partition(A, 1, n)
        call quicksort(A[1..q-1])
        call quicksort(A[q+1..n])
    end
end""",
        language="pseudocode",
        created_at=datetime.utcnow(),
        metadata={
            "description": "Algoritmo de ordenamiento QuickSort",
            "author": "Test Suite"
        }
    )

@pytest.fixture
def sample_analysis(sample_algorithm):
    """Crea un resultado de análisis de ejemplo"""
    return MockAnalysisResult(
        algorithm=sample_algorithm,
        big_o="O(n log n)",
        omega="Ω(n log n)",
        theta="Θ(n log n)",
        space_complexity="O(log n)",
        temporal_recurrence="T(n) = 2T(n/2) + O(n)",
        spatial_recurrence=None,
        line_by_line={
            "1": {"complexity": "O(1)", "executions": 1},
            "2": {"complexity": "O(1)", "executions": 1},
            "3": {"complexity": "O(n)", "executions": "log n"}
        },
        analysis_time=0.123,
        analyzer_version="1.0.0",
        created_at=datetime.utcnow()
    )

@pytest.fixture
def sample_patterns(sample_algorithm):
    """Crea detección de patrones de ejemplo"""
    return MockPatternDetection(
        algorithm=sample_algorithm,
        primary_pattern="divide_and_conquer",
        primary_confidence=0.95,
        patterns_found=[
            {
                "pattern": "divide_and_conquer",
                "confidence": 0.95,
                "evidence": ["Recursive subdivision", "Partition step"]
            },
            {
                "pattern": "recursion",
                "confidence": 1.0,
                "evidence": ["Recursive calls to quicksort"]
            }
        ],
        structures_found=[],
        detection_time=0.234,
        created_at=datetime.utcnow()
    )

# TESTS - ExporterFactory
def test_exporter_factory_get_available_formats():
    """Test que verifica formatos disponibles"""
    formats = ExporterFactory.get_available_formats()
    
    # Formatos siempre disponibles
    assert ExportFormat.JSON in formats
    assert ExportFormat.MARKDOWN in formats
    assert ExportFormat.CSV in formats
    assert ExportFormat.HTML in formats
    
    # Formatos opcionales
    if PDF_AVAILABLE:
        assert ExportFormat.PDF in formats
    if EXCEL_AVAILABLE:
        assert ExportFormat.EXCEL in formats

def test_exporter_factory_is_format_available():
    """Test que verifica disponibilidad de formatos"""
    assert ExporterFactory.is_format_available(ExportFormat.JSON) is True
    assert ExporterFactory.is_format_available(ExportFormat.MARKDOWN) is True

def test_exporter_factory_create_json_exporter():
    """Test creación de exportador JSON"""
    exporter = ExporterFactory.create(ExportFormat.JSON)
    assert exporter is not None
    assert exporter.config.format == ExportFormat.JSON

def test_exporter_factory_create_markdown_exporter():
    """Test creación de exportador Markdown"""
    exporter = ExporterFactory.create(ExportFormat.MARKDOWN)
    assert exporter is not None
    assert exporter.config.format == ExportFormat.MARKDOWN

# TESTS - Exportación JSON
def test_export_to_json(sample_algorithm, sample_analysis, tmp_path):
    """Test exportación a JSON"""
    output_path = tmp_path / "test_export.json"
    
    result = export_analysis(
        algorithm=sample_algorithm,
        analysis=sample_analysis,
        format=ExportFormat.JSON,
        output_path=str(output_path)
    )
    
    assert result.success is True
    assert result.output_path == output_path
    assert output_path.exists()
    
    # Verificar contenido
    import json
    with open(output_path, encoding="utf-8") as f:
        data = json.load(f)
    
    assert "algorithm" in data
    assert "analysis" in data
    assert data["algorithm"]["name"] == "quicksort"
    assert data["analysis"]["complexity"]["big_o"] == "O(n log n)"

# TESTS - Exportación Markdown
def test_export_to_markdown(sample_algorithm, sample_analysis, tmp_path):
    """Test exportación a Markdown"""
    output_path = tmp_path / "test_export.md"
    
    result = export_analysis(
        algorithm=sample_algorithm,
        analysis=sample_analysis,
        format=ExportFormat.MARKDOWN,
        output_path=str(output_path)
    )
    
    assert result.success is True
    assert result.output_path == output_path
    assert output_path.exists()
    
    # Verificar contenido
    content = output_path.read_text(encoding="utf-8")
    assert "# Análisis de Complejidad" in content
    assert "quicksort" in content
    assert "O(n log n)" in content

# TESTS - Exportación con Patrones
def test_export_with_patterns(sample_algorithm, sample_analysis, sample_patterns, tmp_path):
    """Test exportación incluyendo patrones"""
    output_path = tmp_path / "test_with_patterns.json"
    
    result = export_analysis(
        algorithm=sample_algorithm,
        analysis=sample_analysis,
        patterns=sample_patterns,
        format=ExportFormat.JSON,
        output_path=str(output_path)
    )
    
    assert result.success is True
    
    # Verificar que incluye patrones
    import json
    with open(output_path, encoding="utf-8") as f:
        data = json.load(f)
    
    assert "patterns" in data
    assert data["patterns"]["primary"]["name"] == "divide_and_conquer"

# TESTS - Exportación Múltiple
def test_export_to_multiple_formats(sample_algorithm, sample_analysis, tmp_path):
    """Test exportación a múltiples formatos"""
    formats = [ExportFormat.JSON, ExportFormat.MARKDOWN, ExportFormat.CSV]
    
    results = export_to_multiple_formats(
        algorithm=sample_algorithm,
        analysis=sample_analysis,
        formats=formats,
        output_dir=str(tmp_path)
    )
    
    assert len(results) == len(formats)
    
    for format_type, result in results.items():
        assert result.success is True
        if result.output_path is not None:
            assert result.output_path.exists()

# TESTS - Exportación PDF (si está disponible)
@pytest.mark.skipif(not PDF_AVAILABLE, reason="PDF exporter no disponible")
def test_export_to_pdf(sample_algorithm, sample_analysis, tmp_path):
    """Test exportación a PDF"""
    output_path = tmp_path / "test_export.pdf"
    
    result = export_analysis(
        algorithm=sample_algorithm,
        analysis=sample_analysis,
        format=ExportFormat.PDF,
        output_path=str(output_path)
    )
    
    assert result.success is True
    assert result.output_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0  # Archivo no vacío

# TESTS - Exportación Excel (si está disponible)
@pytest.mark.skipif(not EXCEL_AVAILABLE, reason="Excel exporter no disponible")
def test_export_to_excel(sample_algorithm, sample_analysis, tmp_path):
    """Test exportación a Excel"""
    output_path = tmp_path / "test_export.xlsx"
    
    result = export_analysis(
        algorithm=sample_algorithm,
        analysis=sample_analysis,
        format=ExportFormat.EXCEL,
        output_path=str(output_path)
    )
    
    assert result.success is True
    assert result.output_path == output_path
    assert output_path.exists()

# TESTS - Manejo de Errores
def test_export_invalid_format():
    """Test que verifica error con formato inválido"""
    with pytest.raises(ValueError):
        # Intentar crear exportador con formato no soportado
        ExporterFactory.create("invalid_format")

def test_export_without_output_path(sample_algorithm, sample_analysis):
    """Test exportación sin especificar ruta (debe generar automáticamente)"""
    result = export_analysis(
        algorithm=sample_algorithm,
        analysis=sample_analysis,
        format=ExportFormat.JSON
    )
    
    # Debe crear archivo en ubicación temporal
    assert result.success is True
    assert result.output_path is not None

# TESTS DE INTEGRACIÓN
@pytest.mark.integration
def test_full_export_workflow(sample_algorithm, sample_analysis, sample_patterns, tmp_path):
    """Test workflow completo de exportación"""
    # 1. Exportar a JSON
    json_path = tmp_path / "full_export.json"
    json_result = export_analysis(
        algorithm=sample_algorithm,
        analysis=sample_analysis,
        patterns=sample_patterns,
        format=ExportFormat.JSON,
        output_path=str(json_path)
    )
    assert json_result.success
    
    # 2. Exportar a Markdown
    md_path = tmp_path / "full_export.md"
    md_result = export_analysis(
        algorithm=sample_algorithm,
        analysis=sample_analysis,
        patterns=sample_patterns,
        format=ExportFormat.MARKDOWN,
        output_path=str(md_path)
    )
    assert md_result.success
    
    # 3. Verificar ambos archivos
    assert json_path.exists()
    assert md_path.exists()
    
    # 4. Verificar contenido JSON
    import json
    with open(json_path, encoding="utf-8") as f:
        json_data = json.load(f)
    assert "algorithm" in json_data
    assert "analysis" in json_data
    assert "patterns" in json_data
    
    # 5. Verificar contenido Markdown
    md_content = md_path.read_text(encoding="utf-8")
    assert "quicksort" in md_content
    assert "divide_and_conquer" in md_content

if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "--tb=short"])