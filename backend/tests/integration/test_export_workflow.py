"""
Integration Tests - Export Workflow

Prueba el flujo completo de exportación de resultados.
"""

import pytest
from pathlib import Path
from app.infrastructure.export import (
    ExporterFactory,
    ExportFormat,
    ExportConfig,
    ExportData,
    export_analysis,
)

class TestExportWorkflow:
    """Tests del workflow de exportación"""
    
    def test_json_export_workflow(self, temp_output_dir):
        """Test: Workflow completo de export JSON"""
        
        from datetime import datetime
        
        # Mock data
        class MockAlgorithm:
            id = "test123"
            name = "TestAlgorithm"
            code = "algorithm test(n)\nbegin\n    x ← 1\nend"
            category = "other"
            language = "pseudo"
            tags = ["test"]
            description = "Mock algorithm for tests"
            author = "tester"
            created_at = datetime.utcnow()
        
        class MockAnalysis:
            big_o = "O(1)"
            omega = "Ω(1)"
            theta = "Θ(1)"
            space_complexity = "O(1)"
            is_recursive = False
            analyzer_version = "test-analyzer-0.0"
            temporal_recurrence = None
            spatial_recurrence = None
            line_by_line = None
            created_at = datetime.utcnow()
            analysis_time = 0.0
        
        # Export
        output_path = temp_output_dir / "test.json"
        
        result = export_analysis(
            algorithm=MockAlgorithm(),
            analysis=MockAnalysis(),
            format=ExportFormat.JSON,
            output_path=str(output_path)
        )
        
        assert result.success is True
        assert output_path.exists()
        
        # Verificar contenido
        import json
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["algorithm"]["name"] == "TestAlgorithm"
        # JSON exporter nests complexity under 'analysis'
        assert data["analysis"]["complexity"]["big_o"] == "O(1)"
    
    def test_html_export_workflow(self, temp_output_dir):
        """Test: Workflow completo de export HTML"""
        
        from datetime import datetime
        
        class MockAlgorithm:
            id = "test123"
            name = "HTMLTest"
            code = "algorithm test(n)\nbegin\n    for i ← 1 to n do\n    begin\n        x ← i\n    end\nend"
            category = "other"
            language = "pseudo"
            tags = ["html", "test"]
            description = "HTML export mock"
            author = "tester"
            created_at = datetime.utcnow()
        
        class MockAnalysis:
            big_o = "O(n)"
            omega = "Ω(n)"
            theta = "Θ(n)"
            space_complexity = "O(1)"
            is_recursive = False
            analyzer_version = "test-analyzer-0.0"
            temporal_recurrence = None
            spatial_recurrence = None
            line_by_line = None
            created_at = datetime.utcnow()
            analysis_time = 0.0
        
        output_path = temp_output_dir / "test.html"
        
        result = export_analysis(
            algorithm=MockAlgorithm(),
            analysis=MockAnalysis(),
            format=ExportFormat.HTML,
            output_path=str(output_path)
        )
        
        assert result.success is True
        assert output_path.exists()
        
        # Verificar que es HTML válido
        content = output_path.read_text(encoding="utf-8")
        assert "<html" in content.lower()
        assert "HTMLTest" in content
    
    @pytest.mark.parametrize("format_type", [
        ExportFormat.JSON,
        ExportFormat.HTML,
        ExportFormat.CSV,
    ])
    def test_all_basic_formats(self, format_type, temp_output_dir):
        """Test parametrizado: Todos los formatos básicos"""
        
        from datetime import datetime
        
        class MockAlgorithm:
            id = "test"
            name = "FormatTest"
            code = "algorithm test(n)\nbegin\n    x ← 1\nend"
            category = "other"
            language = "pseudo"
            tags = ["format"]
            description = "Format export mock"
            author = "tester"
            created_at = datetime.utcnow()
        
        class MockAnalysis:
            big_o = "O(1)"
            omega = "Ω(1)"
            theta = None
            space_complexity = "O(1)"
            is_recursive = False
            analyzer_version = "test-analyzer-0.0"
            temporal_recurrence = None
            spatial_recurrence = None
            line_by_line = None
            created_at = datetime.utcnow()
            analysis_time = 0.0
        
        output_path = temp_output_dir / f"test.{format_type.value}"
        
        result = export_analysis(
            algorithm=MockAlgorithm(),
            analysis=MockAnalysis(),
            format=format_type,
            output_path=str(output_path)
        )
        
        assert result.success is True
        # CSV exporter may generate multiple files and return them in metadata
        if result.output_path:
            assert Path(result.output_path).exists()
            assert Path(result.output_path).stat().st_size > 0
        else:
            files = result.metadata.get("files_generated", []) if isinstance(result.metadata, dict) else getattr(result.metadata, "files_generated", [])
            assert files
            for p in files:
                assert Path(p).exists()
                assert Path(p).stat().st_size > 0
