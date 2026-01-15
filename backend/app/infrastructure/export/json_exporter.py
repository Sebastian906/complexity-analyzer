"""
JSON Exporter - Exportador a formato JSON

Exporta resultados de análisis a formato JSON con opción
de formato legible o compacto.
"""

import json
import time
from typing import Any, Dict

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportData,
    ExportFormat,
    ExportResult
)

class JSONExporter(BaseExporter):
    """
    Exportador a formato JSON.
    
    Genera archivos JSON con los resultados completos del análisis.
    Soporta formato legible (pretty-print) y compacto.
    """
    
    def get_format(self) -> ExportFormat:
        """Retorna el formato JSON"""
        return ExportFormat.JSON
    
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos a formato JSON.
        
        Args:
            data: Datos a exportar
            
        Returns:
            ExportResult: Resultado de la exportación
        """
        start_time = time.time()
        
        try:
            # Validar datos
            errors = self.validate_data(data)
            if errors:
                return self.create_result(
                    success=False,
                    errors=errors,
                    export_time=time.time() - start_time
                )
            
            # Preparar datos para JSON
            json_data = self._prepare_json_data(data)
            
            # Serializar a JSON
            indent = 2 if self.config.pretty_print else None
            json_content = json.dumps(
                json_data,
                indent=indent,
                ensure_ascii=False,
                default=self._json_serializer
            )
            
            # Guardar o retornar contenido
            output_path = None
            file_size = None
            
            if self.config.output_path or self.config.custom_options.get("save_to_file", True):
                output_path = self.prepare_output_path(data)
                file_size = self.save_to_file(json_content, output_path)
            
            export_time = time.time() - start_time
            
            self.logger.info(f"Exportación JSON completada en {export_time:.3f}s")
            
            return self.create_result(
                success=True,
                output_path=output_path,
                content=json_content if not output_path else None,
                file_size=file_size,
                export_time=export_time,
                data_size=len(json_data),
                structure_depth=self._calculate_depth(json_data)
            )
            
        except Exception as e:
            self.logger.error(f"Error en exportación JSON: {str(e)}")
            return self.create_result(
                success=False,
                errors=[str(e)],
                export_time=time.time() - start_time
            )
    
    def _prepare_json_data(self, data: ExportData) -> Dict[str, Any]:
        """
        Prepara los datos para exportación JSON.
        
        Args:
            data: Datos a preparar
            
        Returns:
            Dict[str, Any]: Datos preparados
        """
        json_data = {
            "metadata": {
                "export_format": "json",
                "export_timestamp": data.timestamp.isoformat(),
                "analyzer_version": data.analysis.analyzer_version,
            }
        }
        
        # Incluir información del algoritmo
        if self.config.include_code:
            json_data["algorithm"] = {
                "name": data.algorithm.name,
                "code": data.algorithm.code,
                "language": data.algorithm.language,
                "category": data.algorithm.category,
                "tags": data.algorithm.tags,
                "description": data.algorithm.description,
                "author": data.algorithm.author,
                "created_at": data.algorithm.created_at.isoformat() if data.algorithm.created_at else None,
            }
        
        # Incluir resultados de análisis
        json_data["analysis"] = {
            "complexity": {
                "big_o": self.format_complexity(data.analysis.big_o),
                "omega": self.format_complexity(data.analysis.omega),
                "theta": self.format_complexity(data.analysis.theta),
                "space": self.format_complexity(data.analysis.space_complexity),
            },
            "recurrence": {
                "temporal": data.analysis.temporal_recurrence,
                "spatial": data.analysis.spatial_recurrence,
            }
        }
        
        # Incluir análisis línea por línea si está disponible
        if data.analysis.line_by_line:
            json_data["analysis"]["line_by_line"] = data.analysis.line_by_line
        
        # Incluir estadísticas
        if self.config.include_statistics:
            json_data["statistics"] = {
                "analysis_time": data.analysis.analysis_time,
                "analysis_timestamp": data.analysis.created_at.isoformat() if data.analysis.created_at else None,
            }
        
        # Incluir patrones detectados
        if data.patterns:
            json_data["patterns"] = {
                "primary": {
                    "name": data.patterns.primary_pattern,
                    "confidence": data.patterns.primary_confidence,
                },
                "all_patterns": data.patterns.patterns_found,
                "structures": data.patterns.structures_found,
                "detection_time": data.patterns.detection_time,
            }
        
        # Incluir visualizaciones
        if self.config.include_visualizations and data.visualizations:
            json_data["visualizations"] = self.extract_visualization_data(
                data.visualizations
            )
        
        return json_data
    
    def _json_serializer(self, obj: Any) -> Any:
        """
        Serializer personalizado para objetos no serializables.
        
        Args:
            obj: Objeto a serializar
            
        Returns:
            Any: Versión serializable del objeto
        """
        # Manejar objetos con to_dict()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        
        # Manejar enums
        if hasattr(obj, "value"):
            return obj.value
        
        # Manejar datetime
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        
        # Por defecto, convertir a string
        return str(obj)
    
    def _calculate_depth(self, data: Dict[str, Any], current_depth: int = 0) -> int:
        """
        Calcula la profundidad de la estructura JSON.
        
        Args:
            data: Datos a analizar
            current_depth: Profundidad actual
            
        Returns:
            int: Profundidad máxima
        """
        if not isinstance(data, dict):
            return current_depth
        
        if not data:
            return current_depth
        
        max_depth = current_depth
        for value in data.values():
            if isinstance(value, dict):
                depth = self._calculate_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        depth = self._calculate_depth(item, current_depth + 1)
                        max_depth = max(max_depth, depth)
        
        return max_depth


def export_to_json(
    data: ExportData,
    output_path: str = None,
    pretty_print: bool = True
) -> ExportResult:
    """
    Helper para exportar a JSON rápidamente.
    
    Args:
        data: Datos a exportar
        output_path: Ruta de salida (opcional)
        pretty_print: Formato legible
        
    Returns:
        ExportResult: Resultado de la exportación
    """
    from pathlib import Path
    from app.infrastructure.export.base_exporter import ExportConfig
    
    config = ExportConfig(
        format=ExportFormat.JSON,
        output_path=Path(output_path) if output_path else None,
        pretty_print=pretty_print
    )
    
    exporter = JSONExporter(config)
    return exporter.export(data)