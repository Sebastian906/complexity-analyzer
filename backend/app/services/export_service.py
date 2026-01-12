"""
Export Service - Servicio de Exportación

Exporta resultados de análisis en múltiples formatos (JSON, PDF, Markdown, etc.)
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Any

from app.core.config import settings
from app.core.exceptions import ExportFormatException
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Enums
class ExportFormat(str, Enum):
    """Formatos de exportación soportados"""
    JSON = "json"
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"
    TXT = "txt"

# DTOs
@dataclass
class ExportOptions:
    """Opciones de exportación"""
    include_code: bool = True
    include_visualizations: bool = True
    include_metadata: bool = True
    include_summary: bool = True
    pretty_print: bool = True

@dataclass
class ExportRequest:
    """Request de exportación"""
    data: Dict[str, Any]
    format: ExportFormat
    options: ExportOptions = field(default_factory=ExportOptions)
    filename: Optional[str] = None
    output_path: Optional[Path] = None

@dataclass
class ExportResult:
    """Resultado de exportación"""
    success: bool
    format: ExportFormat
    content: Optional[str] = None
    file_path: Optional[Path] = None
    size_bytes: int = 0
    error: Optional[str] = None

# Service
class ExportService:
    """
    Servicio de exportación de resultados.

    Exporta análisis en múltiples formatos para diferentes usos.

    Example:
        >>> service = ExportService()
        >>> request = ExportRequest(
        ...     data={"algorithm": "test", "complexity": "O(n)"},
        ...     format=ExportFormat.JSON
        ... )
        >>> result = await service.export(request)
    """

    def __init__(self, export_path: Optional[Path] = None):
        self.export_path = export_path or settings.EXPORTS_PATH
        self.export_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"ExportService inicializado - Path: {self.export_path}")

    async def export(self, request: ExportRequest) -> ExportResult:
        """Exporta datos en formato especificado"""
        logger.info(f"Exportando en formato: {request.format}")

        try:
            # Seleccionar exportador
            if request.format == ExportFormat.JSON:
                content = await self._export_json(request)
            elif request.format == ExportFormat.MARKDOWN:
                content = await self._export_markdown(request)
            elif request.format == ExportFormat.TXT:
                content = await self._export_text(request)
            elif request.format == ExportFormat.HTML:
                content = await self._export_html(request)
            elif request.format == ExportFormat.PDF:
                return await self._export_pdf(request)
            else:
                raise ExportFormatException(
                    request.format.value,
                    [f.value for f in ExportFormat]
                )

            # Guardar archivo si se especifica path
            file_path = None
            if request.output_path or request.filename:
                file_path = await self._save_file(
                    content,
                    request.format,
                    request.filename,
                    request.output_path
                )

            return ExportResult(
                success=True,
                format=request.format,
                content=content,
                file_path=file_path,
                size_bytes=len(content.encode('utf-8')) if content else 0
            )

        except Exception as e:
            logger.error(f"Error en exportación: {e}", exc_info=True)
            return ExportResult(
                success=False,
                format=request.format,
                error=str(e)
            )

    async def _export_json(self, request: ExportRequest) -> str:
        """Exporta a JSON"""
        data = request.data.copy()

        if request.options.include_metadata:
            data["_metadata"] = {
                "exported_at": datetime.utcnow().isoformat(),
                "format": "json",
                "version": "1.0"
            }

        indent = 2 if request.options.pretty_print else None
        return json.dumps(data, indent=indent, default=str, ensure_ascii=False)

    async def _export_markdown(self, request: ExportRequest) -> str:
        """Exporta a Markdown"""
        lines = ["# Reporte de Análisis de Algoritmo", ""]

        data = request.data

        # Algoritmo
        if "algorithm_name" in data:
            lines.append(f"**Algoritmo:** {data['algorithm_name']}")
            lines.append("")

        # Complejidad
        if "complexity_result" in data:
            comp = data["complexity_result"]
            lines.append("## Complejidad")
            lines.append(f"- **Big O:** {comp.get('big_o', 'N/A')}")
            lines.append(f"- **Omega:** {comp.get('omega', 'N/A')}")
            lines.append(f"- **Theta:** {comp.get('theta', 'N/A')}")
            lines.append("")

        # Patrón
        if "patterns_result" in data and data["patterns_result"].get("primary_pattern"):
            pattern = data["patterns_result"]["primary_pattern"]
            lines.append("## Patrón Detectado")
            lines.append(f"**{pattern['name']}** (confianza: {pattern['confidence']:.2%})")
            lines.append("")

        # Summary
        if request.options.include_summary and "summary" in data:
            lines.append("## Resumen")
            lines.append("```")
            lines.append(data["summary"])
            lines.append("```")

        return "\n".join(lines)

    async def _export_text(self, request: ExportRequest) -> str:
        """Exporta a texto plano"""
        lines = ["=" * 60, "REPORTE DE ANÁLISIS", "=" * 60, ""]

        data = request.data

        if "algorithm_name" in data:
            lines.append(f"Algoritmo: {data['algorithm_name']}")
            lines.append("")

        if "complexity_result" in data:
            comp = data["complexity_result"]
            lines.append("COMPLEJIDAD:")
            lines.append(f"  Big O:  {comp.get('big_o', 'N/A')}")
            lines.append(f"  Omega:  {comp.get('omega', 'N/A')}")
            lines.append(f"  Theta:  {comp.get('theta', 'N/A')}")
            lines.append("")

        return "\n".join(lines)

    async def _export_html(self, request: ExportRequest) -> str:
        """Exporta a HTML"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reporte de Análisis</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #2c3e50; }
        .complexity { background: #ecf0f1; padding: 15px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Reporte de Análisis de Algoritmo</h1>
"""

        data = request.data

        if "algorithm_name" in data:
            html += f"    <h2>{data['algorithm_name']}</h2>\n"

        if "complexity_result" in data:
            comp = data["complexity_result"]
            html += "    <div class='complexity'>\n"
            html += "        <h3>Complejidad</h3>\n"
            html += f"        <p><strong>Big O:</strong> {comp.get('big_o', 'N/A')}</p>\n"
            html += f"        <p><strong>Omega:</strong> {comp.get('omega', 'N/A')}</p>\n"
            html += f"        <p><strong>Theta:</strong> {comp.get('theta', 'N/A')}</p>\n"
            html += "    </div>\n"

        html += "</body>\n</html>"
        return html

    async def _export_pdf(self, request: ExportRequest) -> ExportResult:
        """Exporta a PDF (placeholder - requiere reportlab)"""
        logger.warning("Exportación PDF no completamente implementada")

        # Placeholder: convertir markdown a PDF requeriría reportlab
        # Por ahora retornar error informativo
        return ExportResult(
            success=False,
            format=ExportFormat.PDF,
            error="Exportación PDF pendiente de implementación completa en Módulo 6"
        )

    async def _save_file(
        self,
        content: str,
        format: ExportFormat,
        filename: Optional[str],
        output_path: Optional[Path]
    ) -> Path:
        """Guarda contenido en archivo"""
        if output_path:
            file_path = output_path
        else:
            # Generar nombre si no se proporciona
            if not filename:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"export_{timestamp}.{format.value}"

            # Determinar subdirectorio por formato
            subdir = self.export_path / format.value
            subdir.mkdir(exist_ok=True)

            file_path = subdir / filename

        # Guardar
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"Archivo guardado: {file_path}")

        return file_path