"""
Export Module - Sistema de exportación de resultados

Proporciona exportadores para múltiples formatos:
- JSON: Datos estructurados (.json)
- Markdown: Documentación (.md)
- PDF: Reportes profesionales (.pdf)
- Excel: Análisis de datos (.xlsx)  
- HTML: Visualización web (.html)
- CSV: Datos tabulares (.csv)
- DOT: Visualización con Graphviz (.dot)
- Mermaid: Diagramas en Markdown (.mmd)  
- SVG: Gráficos vectoriales (.svg)

Uso básico:
    from app.infrastructure.export import export_analysis, ExportFormat
    
    result = export_analysis(
        algorithm=algorithm,
        analysis=analysis_result,
        patterns=pattern_detection,
        format=ExportFormat.PDF,
        output_path="output.pdf"
    )
"""

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportConfig,
    ExportData,
    ExportFormat,
    ExportResult
)

from app.infrastructure.export.json_exporter import JSONExporter, export_to_json
from app.infrastructure.export.markdown_exporter import MarkdownExporter, export_to_markdown
from app.infrastructure.export.csv_exporter import CSVExporter, export_to_csv
from app.infrastructure.export.dot_exporter import DOTExporter, export_to_dot
from app.infrastructure.export.mermaid_exporter import MermaidExporter, export_to_mermaid
from app.infrastructure.export.svg_exporter import SVGExporter, export_to_svg
from app.infrastructure.export.html_exporter import HTMLExporter, export_to_html
from app.infrastructure.export.txt_exporter import TXTExporter, export_to_txt

# PDF y Excel son opcionales (requieren librerías externas)
try:
    from app.infrastructure.export.pdf_exporter import PDFExporter, export_to_pdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from app.infrastructure.export.excel_exporter import ExcelExporter, export_to_excel
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

class ExporterFactory:
    """
    Factory para crear exportadores según formato.
    
    Simplifica la creación de exportadores y maneja dependencias opcionales.
    """
    
    # Registro de exportadores
    _exporters = {
        ExportFormat.JSON: JSONExporter,
        ExportFormat.MARKDOWN: MarkdownExporter,
        ExportFormat.CSV: CSVExporter,
        ExportFormat.DOT: DOTExporter,
        ExportFormat.MERMAID: MermaidExporter,
        ExportFormat.SVG: SVGExporter,
        ExportFormat.HTML: HTMLExporter,
        ExportFormat.TXT: TXTExporter,
    }
    
    if PDF_AVAILABLE:
        _exporters[ExportFormat.PDF] = PDFExporter
    
    if EXCEL_AVAILABLE:
        _exporters[ExportFormat.EXCEL] = ExcelExporter
    
    @classmethod
    def create(
        cls,
        format: ExportFormat,
        config: ExportConfig = None
    ) -> BaseExporter:
        """
        Crea un exportador para el formato especificado.
        
        Args:
            format: Formato de exportación
            config: Configuración (opcional)
            
        Returns:
            BaseExporter: Instancia del exportador
            
        Raises:
            ValueError: Si el formato no es soportado
            ImportError: Si faltan dependencias opcionales
        """
        if format not in cls._exporters:
            if format == ExportFormat.PDF and not PDF_AVAILABLE:
                raise ImportError(
                    "PDF export requiere reportlab. "
                    "Instala con: pip install reportlab"
                )
            elif format == ExportFormat.EXCEL and not EXCEL_AVAILABLE:
                raise ImportError(
                    "Excel export requiere openpyxl. "
                    "Instala con: pip install openpyxl"
                )
            else:
                raise ValueError(f"Formato no soportado: {format}")
        
        exporter_class = cls._exporters[format]
        
        if config is None:
            config = ExportConfig(format=format)
        
        return exporter_class(config)
    
    @classmethod
    def get_available_formats(cls) -> list:
        """
        Retorna lista de formatos disponibles.
        
        Returns:
            list: Lista de ExportFormat disponibles
        """
        return list(cls._exporters.keys())
    
    @classmethod
    def is_format_available(cls, format: ExportFormat) -> bool:
        """
        Verifica si un formato está disponible.
        
        Args:
            format: Formato a verificar
            
        Returns:
            bool: True si está disponible
        """
        return format in cls._exporters

def export_analysis(
    algorithm,
    analysis,
    patterns=None,
    visualizations=None,
    format: ExportFormat = ExportFormat.JSON,
    output_path: str = None,
    **kwargs
) -> ExportResult:
    """
    Función helper para exportar análisis completo.
    
    Args:
        algorithm: Instancia de Algorithm (MongoDB model)
        analysis: Instancia de AnalysisResult (MongoDB model)
        patterns: Instancia de PatternDetection (opcional)
        visualizations: Dict con visualizaciones (opcional)
        format: Formato de exportación
        output_path: Ruta de salida (opcional)
        **kwargs: Opciones adicionales para ExportConfig
        
    Returns:
        ExportResult: Resultado de la exportación
        
    Example:
        result = export_analysis(
            algorithm=algo,
            analysis=analysis_result,
            patterns=patterns,
            format=ExportFormat.PDF,
            output_path="report.pdf"
        )
        
        if result.success:
            print(f"Exportado a: {result.output_path}")
        else:
            print(f"Errores: {result.errors}")
    """
    from pathlib import Path
    
    # Crear datos de exportación
    export_data = ExportData(
        algorithm=algorithm,
        analysis=analysis,
        patterns=patterns,
        visualizations=visualizations or {}
    )
    
    # Crear configuración
    config = ExportConfig(
        format=format,
        output_path=Path(output_path) if output_path else None,
        **kwargs
    )
    
    # Crear exportador y exportar
    exporter = ExporterFactory.create(format, config)
    return exporter.export(export_data)

def export_to_multiple_formats(
    algorithm,
    analysis,
    patterns=None,
    visualizations=None,
    formats: list = None,
    output_dir: str = None
) -> dict:
    """
    Exporta a múltiples formatos simultáneamente.
    
    Args:
        algorithm: Instancia de Algorithm
        analysis: Instancia de AnalysisResult
        patterns: Instancia de PatternDetection (opcional)
        visualizations: Dict con visualizaciones (opcional)
        formats: Lista de formatos (por defecto: todos disponibles)
        output_dir: Directorio de salida (opcional)
        
    Returns:
        dict: Diccionario {formato: ExportResult}
        
    Example:
        results = export_to_multiple_formats(
            algorithm=algo,
            analysis=analysis_result,
            formats=[ExportFormat.JSON, ExportFormat.PDF, ExportFormat.HTML]
        )
        
        for format, result in results.items():
            if result.success:
                print(f"{format}: ✓ {result.output_path}")
            else:
                print(f"{format}: ✗ {result.errors}")
    """
    from pathlib import Path
    
    if formats is None:
        formats = ExporterFactory.get_available_formats()
    
    results = {}
    
    for export_format in formats:
        try:
            # Determinar ruta de salida
            output_path = None
            if output_dir:
                base_name = algorithm.name
                extension = export_format.value
                output_path = Path(output_dir) / f"{base_name}.{extension}"
            
            result = export_analysis(
                algorithm=algorithm,
                analysis=analysis,
                patterns=patterns,
                visualizations=visualizations,
                format=export_format,
                output_path=str(output_path) if output_path else None
            )
            
            results[export_format] = result
            
        except Exception as e:
            # En caso de error, crear resultado con error
            results[export_format] = ExportResult(
                success=False,
                format=export_format,
                errors=[str(e)]
            )
    
    return results

__all__ = [
    # Base classes
    "BaseExporter",
    "ExportConfig",
    "ExportData",
    "ExportFormat",
    "ExportResult",
    
    # Exporters (always available)
    "JSONExporter",
    "MarkdownExporter",
    "CSVExporter",
    "DOTExporter",
    "MermaidExporter",
    "SVGExporter",
    "HTMLExporter",
    "TXTExporter",
    
    # Optional exporters
    "PDFExporter",  # Puede no estar disponible
    "ExcelExporter",  # Puede no estar disponible
    
    # Helper functions
    "export_to_json",
    "export_to_markdown",
    "export_to_csv",
    "export_to_dot",
    "export_to_mermaid",
    "export_to_svg",
    "export_to_html",
    "export_to_txt",
    "export_to_pdf",  # Puede no estar disponible
    "export_to_excel",  # Puede no estar disponible
    
    # Factory and utilities
    "ExporterFactory",
    "export_analysis",
    "export_to_multiple_formats",
    
    # Flags
    "PDF_AVAILABLE",
    "EXCEL_AVAILABLE",
]