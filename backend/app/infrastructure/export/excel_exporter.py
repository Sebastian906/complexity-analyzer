"""
Excel Exporter - Exportador a formato Excel

Exporta resultados de análisis a Excel (.xlsx)
con múltiples hojas y formato profesional.
"""

import time
from typing import Dict, Any, List

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, Reference
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportData,
    ExportFormat,
    ExportResult
)

class ExcelExporter(BaseExporter):
    """
    Exportador a formato Excel (.xlsx).
    
    Genera archivos Excel con:
    - Múltiples hojas de trabajo
    - Formato profesional
    - Gráficos integrados
    - Tablas dinámicas
    
    Requiere: openpyxl
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not OPENPYXL_AVAILABLE:
            raise ImportError(
                "openpyxl no está instalado. "
                "Instala con: pip install openpyxl"
            )
    
    def get_format(self) -> ExportFormat:
        """Retorna el formato Excel"""
        return ExportFormat.EXCEL
    
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos a formato Excel.
        
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
            
            # Crear workbook
            wb = Workbook()
            wb.remove(wb.active)  # Eliminar hoja por defecto
            
            # Crear hojas
            self._create_summary_sheet(wb, data)
            self._create_complexity_sheet(wb, data)
            
            if data.patterns:
                self._create_patterns_sheet(wb, data)
                self._create_structures_sheet(wb, data)
            
            if data.analysis.line_by_line:
                self._create_line_analysis_sheet(wb, data)
            
            if self.config.include_code:
                self._create_code_sheet(wb, data)
            
            # Guardar archivo
            output_path = self.prepare_output_path(data)
            wb.save(str(output_path))
            
            file_size = output_path.stat().st_size
            export_time = time.time() - start_time
            
            self.logger.info(f"Exportación Excel completada en {export_time:.3f}s")
            
            return self.create_result(
                success=True,
                output_path=output_path,
                file_size=file_size,
                export_time=export_time,
                sheets_count=len(wb.sheetnames)
            )
            
        except Exception as e:
            self.logger.error(f"Error en exportación Excel: {str(e)}")
            return self.create_result(
                success=False,
                errors=[str(e)],
                export_time=time.time() - start_time
            )
    
    def _create_summary_sheet(self, wb: Workbook, data: ExportData):
        """Crea hoja de resumen"""
        ws = wb.create_sheet("Resumen")
        
        # Estilos
        header_font = Font(size=14, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
        title_font = Font(size=18, bold=True, color="667EEA")
        
        # Título
        ws['A1'] = data.algorithm.name
        ws['A1'].font = title_font
        ws.merge_cells('A1:D1')
        
        ws['A2'] = "Análisis de Complejidad Algorítmica"
        ws['A2'].font = Font(size=12, italic=True)
        ws.merge_cells('A2:D2')
        
        # Información general
        row = 4
        info_data = [
            ("Información General", ""),
            ("Lenguaje:", data.algorithm.language),
            ("Categoría:", data.algorithm.category or "No especificada"),
            ("Tiempo de análisis:", f"{data.analysis.analysis_time:.3f}s"),
            ("Fecha de análisis:", self.format_timestamp(data.analysis.created_at)),
            ("Versión analizador:", data.analysis.analyzer_version),
        ]
        
        if data.algorithm.author:
            info_data.insert(3, ("Autor:", data.algorithm.author))
        
        for label, value in info_data:
            ws[f'A{row}'] = label
            ws[f'B{row}'] = value
            
            if not value:  # Es encabezado de sección
                ws[f'A{row}'].font = Font(bold=True, size=12)
                ws.merge_cells(f'A{row}:B{row}')
            
            row += 1
        
        # Complejidades principales
        row += 1
        ws[f'A{row}'] = "Complejidades"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        ws.merge_cells(f'A{row}:B{row}')
        row += 1
        
        complexity_data = [
            ("Big O (Peor caso):", self.format_complexity(data.analysis.big_o)),
            ("Omega (Mejor caso):", self.format_complexity(data.analysis.omega)),
        ]
        
        if data.analysis.theta:
            complexity_data.append(
                ("Theta (Promedio):", self.format_complexity(data.analysis.theta))
            )
        
        if data.analysis.space_complexity:
            complexity_data.append(
                ("Espacial:", self.format_complexity(data.analysis.space_complexity))
            )
        
        for label, value in complexity_data:
            ws[f'A{row}'] = label
            ws[f'B{row}'] = value
            ws[f'B{row}'].font = Font(name='Courier New', bold=True, size=11)
            row += 1
        
        # Patrón principal
        if data.patterns:
            row += 1
            ws[f'A{row}'] = "Patrón Principal"
            ws[f'A{row}'].font = Font(bold=True, size=12)
            ws.merge_cells(f'A{row}:B{row}')
            row += 1
            
            ws[f'A{row}'] = data.patterns.primary_pattern
            ws[f'B{row}'] = f"{data.patterns.primary_confidence:.1%}"
            row += 1
        
        # Ajustar anchos de columna
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 30
    
    def _create_complexity_sheet(self, wb: Workbook, data: ExportData):
        """Crea hoja de análisis de complejidad"""
        ws = wb.create_sheet("Complejidad")
        
        # Encabezados
        headers = ["Notación", "Caso", "Complejidad", "Descripción"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Datos
        complexity_rows = [
            ("Big O (O)", "Peor caso", self.format_complexity(data.analysis.big_o), 
             "Máximo tiempo de ejecución"),
            ("Omega (Ω)", "Mejor caso", self.format_complexity(data.analysis.omega),
             "Mínimo tiempo de ejecución"),
        ]
        
        if data.analysis.theta:
            complexity_rows.append(
                ("Theta (Θ)", "Caso promedio", self.format_complexity(data.analysis.theta),
                 "Tiempo de ejecución promedio")
            )
        
        if data.analysis.space_complexity:
            complexity_rows.append(
                ("Espacio", "Memoria", self.format_complexity(data.analysis.space_complexity),
                 "Espacio de memoria requerido")
            )
        
        for row_idx, row_data in enumerate(complexity_rows, 2):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                if col_idx == 3:  # Columna de complejidad
                    cell.font = Font(name='Courier New', bold=True)
        
        # Ecuaciones de recurrencia
        if data.analysis.temporal_recurrence or data.analysis.spatial_recurrence:
            row = len(complexity_rows) + 3
            
            ws.cell(row=row, column=1, value="Ecuaciones de Recurrencia").font = Font(bold=True, size=12)
            row += 1
            
            if data.analysis.temporal_recurrence:
                ws.cell(row=row, column=1, value="Temporal:")
                ws.cell(row=row, column=2, value=data.analysis.temporal_recurrence)
                ws.cell(row=row, column=2).font = Font(name='Courier New')
                row += 1
            
            if data.analysis.spatial_recurrence:
                ws.cell(row=row, column=1, value="Espacial:")
                ws.cell(row=row, column=2, value=data.analysis.spatial_recurrence)
                ws.cell(row=row, column=2).font = Font(name='Courier New')
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 40
    
    def _create_patterns_sheet(self, wb: Workbook, data: ExportData):
        """Crea hoja de patrones detectados"""
        if not data.patterns or not data.patterns.patterns_found:
            return
        
        ws = wb.create_sheet("Patrones")
        
        # Encabezados
        headers = ["Patrón", "Confianza", "Score", "Evidencias"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="87CEEB", end_color="87CEEB", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Datos
        for row_idx, pattern in enumerate(data.patterns.patterns_found, 2):
            name = pattern.get("name", "Desconocido")
            confidence = pattern.get("confidence", 0)
            score = pattern.get("score", 0)
            evidence = pattern.get("evidence", [])
            
            ws.cell(row=row_idx, column=1, value=name)
            ws.cell(row=row_idx, column=2, value=f"{confidence:.1%}")
            ws.cell(row=row_idx, column=3, value=f"{score:.4f}")
            ws.cell(row=row_idx, column=4, value=len(evidence))
            
            # Formato condicional para confianza
            conf_cell = ws.cell(row=row_idx, column=2)
            if confidence >= 0.8:
                conf_cell.fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
            elif confidence >= 0.5:
                conf_cell.fill = PatternFill(start_color="FFD93D", end_color="FFD93D", fill_type="solid")
            else:
                conf_cell.fill = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 15
    
    def _create_structures_sheet(self, wb: Workbook, data: ExportData):
        """Crea hoja de estructuras de datos"""
        if not data.patterns or not data.patterns.structures_found:
            return
        
        ws = wb.create_sheet("Estructuras")
        
        # Encabezados
        headers = ["Estructura", "Confianza", "Operaciones", "Complejidad Temporal"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="B19CD9", end_color="B19CD9", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Datos
        for row_idx, structure in enumerate(data.patterns.structures_found, 2):
            name = structure.get("name", "Desconocida")
            confidence = structure.get("confidence", 0)
            operations = structure.get("operations", [])
            time_comp = structure.get("time_complexity", {})
            
            ws.cell(row=row_idx, column=1, value=name)
            ws.cell(row=row_idx, column=2, value=f"{confidence:.1%}")
            ws.cell(row=row_idx, column=3, value=", ".join(operations) if operations else "N/A")
            
            # Formatear complejidades temporales
            if isinstance(time_comp, dict):
                comp_str = "; ".join([f"{op}: {comp}" for op, comp in time_comp.items()])
                ws.cell(row=row_idx, column=4, value=comp_str)
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 40
    
    def _create_line_analysis_sheet(self, wb: Workbook, data: ExportData):
        """Crea hoja de análisis línea por línea"""
        ws = wb.create_sheet("Línea por Línea")
        
        # Encabezados
        headers = ["Línea", "Código", "Complejidad", "Ejecuciones"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="FFD93D", end_color="FFD93D", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Datos
        line_data = data.analysis.line_by_line
        
        if isinstance(line_data, dict):
            for row_idx, (line_num, info) in enumerate(sorted(line_data.items()), 2):
                code = info.get("code", "").strip()
                complexity = info.get("complexity", "O(1)")
                executions = info.get("executions", "1")
                
                ws.cell(row=row_idx, column=1, value=str(line_num))
                ws.cell(row=row_idx, column=2, value=code)
                ws.cell(row=row_idx, column=3, value=complexity)
                ws.cell(row=row_idx, column=4, value=str(executions))
                
                # Formato
                ws.cell(row=row_idx, column=2).font = Font(name='Courier New', size=9)
                ws.cell(row=row_idx, column=3).font = Font(name='Courier New', bold=True)
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 60
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
    
    def _create_code_sheet(self, wb: Workbook, data: ExportData):
        """Crea hoja con código fuente"""
        ws = wb.create_sheet("Código")
        
        # Título
        ws['A1'] = "Código Fuente"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:B1')
        
        # Código
        code_lines = data.algorithm.code.split('\n')
        for idx, line in enumerate(code_lines, 3):
            ws.cell(row=idx, column=1, value=idx - 2)  # Número de línea
            ws.cell(row=idx, column=2, value=line)
            ws.cell(row=idx, column=2).font = Font(name='Courier New', size=10)
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 6
        ws.column_dimensions['B'].width = 80

def export_to_excel(
    data: ExportData,
    output_path: str = None
) -> ExportResult:
    """
    Helper para exportar a Excel rápidamente.
    
    Args:
        data: Datos a exportar
        output_path: Ruta de salida (opcional)
        
    Returns:
        ExportResult: Resultado de la exportación
    """
    from pathlib import Path
    from app.infrastructure.export.base_exporter import ExportConfig
    
    config = ExportConfig(
        format=ExportFormat.EXCEL,
        output_path=Path(output_path) if output_path else None
    )
    
    exporter = ExcelExporter(config)
    return exporter.export(data)