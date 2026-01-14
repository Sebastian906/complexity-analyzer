"""
CSV Exporter - Exportador a formato CSV

Exporta resultados de análisis a formato CSV
ideal para análisis de datos, Excel, y herramientas estadísticas.
"""

import csv
import time
from io import StringIO
from typing import List, Dict, Any

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportData,
    ExportFormat,
    ExportResult
)

class CSVExporter(BaseExporter):
    """
    Exportador a formato CSV.
    
    Genera archivos CSV con:
    - Resumen de complejidades
    - Análisis línea por línea
    - Patrones detectados
    - Estructuras de datos
    """
    
    def get_format(self) -> ExportFormat:
        """Retorna el formato CSV"""
        return ExportFormat.CSV
    
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos a formato CSV.
        
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
            
            # Generar múltiples CSVs según configuración
            csv_files = {}
            
            # CSV principal con resumen
            summary_csv = self._generate_summary_csv(data)
            csv_files["summary"] = summary_csv
            
            # CSV de análisis línea por línea
            if data.analysis.line_by_line:
                line_csv = self._generate_line_analysis_csv(data)
                csv_files["line_analysis"] = line_csv
            
            # CSV de patrones
            if data.patterns and data.patterns.patterns_found:
                patterns_csv = self._generate_patterns_csv(data)
                csv_files["patterns"] = patterns_csv
            
            # CSV de estructuras
            if data.patterns and data.patterns.structures_found:
                structures_csv = self._generate_structures_csv(data)
                csv_files["structures"] = structures_csv
            
            # Guardar archivos
            results = []
            total_size = 0
            
            for name, content in csv_files.items():
                if self.config.output_path:
                    base_path = self.prepare_output_path(data)
                    output_path = base_path.parent / f"{base_path.stem}_{name}.csv"
                else:
                    output_path = self.prepare_output_path(data)
                    output_path = output_path.parent / f"{data.algorithm.name}_{name}.csv"
                
                file_size = self.save_to_file(content, output_path)
                total_size += file_size
                results.append(str(output_path))
            
            export_time = time.time() - start_time
            
            self.logger.info(f"Exportación CSV completada: {len(csv_files)} archivos en {export_time:.3f}s")
            
            return self.create_result(
                success=True,
                output_path=None,  # Múltiples archivos
                file_size=total_size,
                export_time=export_time,
                files_generated=results,
                csv_count=len(csv_files)
            )
            
        except Exception as e:
            self.logger.error(f"Error en exportación CSV: {str(e)}")
            return self.create_result(
                success=False,
                errors=[str(e)],
                export_time=time.time() - start_time
            )
    
    def _generate_summary_csv(self, data: ExportData) -> str:
        """
        Genera CSV con resumen del análisis.
        
        Args:
            data: Datos del análisis
            
        Returns:
            str: Contenido CSV
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            "Algoritmo",
            "Lenguaje",
            "Categoría",
            "Big O",
            "Omega",
            "Theta",
            "Espacio",
            "Tiempo Análisis (s)",
            "Patrón Principal",
            "Confianza Patrón"
        ])
        
        # Datos
        writer.writerow([
            data.algorithm.name,
            data.algorithm.language,
            data.algorithm.category or "N/A",
            self.format_complexity(data.analysis.big_o),
            self.format_complexity(data.analysis.omega),
            self.format_complexity(data.analysis.theta) if data.analysis.theta else "N/A",
            self.format_complexity(data.analysis.space_complexity) if data.analysis.space_complexity else "N/A",
            f"{data.analysis.analysis_time:.3f}",
            data.patterns.primary_pattern if data.patterns else "N/A",
            f"{data.patterns.primary_confidence:.2f}" if data.patterns else "N/A"
        ])
        
        return output.getvalue()
    
    def _generate_line_analysis_csv(self, data: ExportData) -> str:
        """
        Genera CSV con análisis línea por línea.
        
        Args:
            data: Datos del análisis
            
        Returns:
            str: Contenido CSV
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            "Línea",
            "Código",
            "Complejidad",
            "Ejecuciones",
            "Tipo"
        ])
        
        # Datos
        line_data = data.analysis.line_by_line
        
        if isinstance(line_data, dict):
            for line_num, info in sorted(line_data.items()):
                code = info.get("code", "").strip()
                complexity = info.get("complexity", "O(1)")
                executions = info.get("executions", "1")
                line_type = info.get("type", "statement")
                
                writer.writerow([
                    line_num,
                    code,
                    complexity,
                    executions,
                    line_type
                ])
        
        return output.getvalue()
    
    def _generate_patterns_csv(self, data: ExportData) -> str:
        """
        Genera CSV con patrones detectados.
        
        Args:
            data: Datos del análisis
            
        Returns:
            str: Contenido CSV
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            "Patrón",
            "Confianza",
            "Score",
            "Evidencias",
            "Características"
        ])
        
        # Datos
        for pattern in data.patterns.patterns_found:
            name = pattern.get("name", "Desconocido")
            confidence = pattern.get("confidence", 0)
            score = pattern.get("score", 0)
            evidence = pattern.get("evidence", [])
            
            # Extraer características de evidencia
            characteristics = []
            for ev in evidence:
                if isinstance(ev, dict):
                    characteristics.append(ev.get("feature", ""))
                else:
                    characteristics.append(str(ev))
            
            writer.writerow([
                name,
                f"{confidence:.4f}",
                f"{score:.4f}",
                len(evidence),
                "; ".join(characteristics)
            ])
        
        return output.getvalue()
    
    def _generate_structures_csv(self, data: ExportData) -> str:
        """
        Genera CSV con estructuras de datos detectadas.
        
        Args:
            data: Datos del análisis
            
        Returns:
            str: Contenido CSV
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            "Estructura",
            "Confianza",
            "Operaciones",
            "Complejidad Temporal",
            "Complejidad Espacial"
        ])
        
        # Datos
        for structure in data.patterns.structures_found:
            name = structure.get("name", "Desconocida")
            confidence = structure.get("confidence", 0)
            operations = structure.get("operations", [])
            time_complexity = structure.get("time_complexity", {})
            space_complexity = structure.get("space_complexity", "N/A")
            
            # Formatear complejidades temporales
            time_complexities = []
            if isinstance(time_complexity, dict):
                for op, comp in time_complexity.items():
                    time_complexities.append(f"{op}: {comp}")
            
            writer.writerow([
                name,
                f"{confidence:.4f}",
                "; ".join(operations) if operations else "N/A",
                "; ".join(time_complexities) if time_complexities else "N/A",
                space_complexity
            ])
        
        return output.getvalue()

def export_to_csv(
    data: ExportData,
    output_path: str = None
) -> ExportResult:
    """
    Helper para exportar a CSV rápidamente.
    
    Args:
        data: Datos a exportar
        output_path: Ruta de salida (opcional)
        
    Returns:
        ExportResult: Resultado de la exportación
    """
    from pathlib import Path
    from app.infrastructure.export.base_exporter import ExportConfig
    
    config = ExportConfig(
        format=ExportFormat.CSV,
        output_path=Path(output_path) if output_path else None
    )
    
    exporter = CSVExporter(config)
    return exporter.export(data)