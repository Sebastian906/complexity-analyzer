"""
PDF Exporter - Exportador a formato PDF

Exporta resultados de análisis a PDF profesional
usando ReportLab para máxima calidad.
"""

import time
from typing import List, Tuple
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image as RLImage
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportData,
    ExportFormat,
    ExportResult
)

class PDFExporter(BaseExporter):
    """
    Exportador a formato PDF.
    
    Genera reportes PDF profesionales con:
    - Diseño estructurado
    - Tablas formateadas
    - Gráficos integrados
    - Estilos personalizados
    
    Requiere: reportlab
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab no está instalado. "
                "Instala con: pip install reportlab"
            )
    
    def get_format(self) -> ExportFormat:
        """Retorna el formato PDF"""
        return ExportFormat.PDF
    
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos a formato PDF.
        
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
            
            # Preparar ruta de salida
            output_path = self.prepare_output_path(data)
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )
            
            # Generar contenido
            story = []
            styles = self._create_custom_styles()
            
            # Agregar secciones
            story.extend(self._generate_title_page(data, styles))
            story.append(PageBreak())
            
            story.extend(self._generate_summary(data, styles))
            story.append(Spacer(1, 0.3*inch))
            
            if self.config.include_code:
                story.extend(self._generate_code_section(data, styles))
                story.append(Spacer(1, 0.3*inch))
            
            story.extend(self._generate_complexity_section(data, styles))
            story.append(Spacer(1, 0.3*inch))
            
            if data.patterns:
                story.extend(self._generate_patterns_section(data, styles))
                story.append(Spacer(1, 0.3*inch))
            
            if data.analysis.line_by_line:
                story.extend(self._generate_line_analysis_section(data, styles))
            
            # Construir PDF
            doc.build(story)
            
            file_size = output_path.stat().st_size
            export_time = time.time() - start_time
            
            self.logger.info(f"Exportación PDF completada en {export_time:.3f}s")
            
            return self.create_result(
                success=True,
                output_path=output_path,
                file_size=file_size,
                export_time=export_time,
                pages_count=len(story)
            )
            
        except Exception as e:
            self.logger.error(f"Error en exportación PDF: {str(e)}")
            return self.create_result(
                success=False,
                errors=[str(e)],
                export_time=time.time() - start_time
            )
    
    def _create_custom_styles(self):
        """Crea estilos personalizados para el PDF"""
        styles = getSampleStyleSheet()
        
        # Título principal
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo
        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.grey,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Encabezado de sección
        if 'SectionHeading' not in styles:
            styles.add(ParagraphStyle(
                name='SectionHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#667eea'),
                spaceAfter=12,
                spaceBefore=12,
                fontName='Helvetica-Bold',
                borderWidth=0,
                borderColor=colors.HexColor('#667eea'),
                borderPadding=5,
                leftIndent=0,
                borderRadius=2
            ))
        # Texto de código
        if 'Code' not in styles:
            styles.add(ParagraphStyle(
                name='Code',
                parent=styles['Code'],
                fontSize=9,
                fontName='Courier',
                textColor=colors.black,
                backColor=colors.HexColor('#f5f5f5'),
                borderWidth=1,
                borderColor=colors.grey,
                borderPadding=10,
                leftIndent=10,
                rightIndent=10
            ))
        return styles
    
    def _generate_title_page(self, data: ExportData, styles) -> List:
        """Genera página de título"""
        story = []
        
        # Espacio superior
        story.append(Spacer(1, 2*inch))
        
        # Título
        story.append(Paragraph(
            data.algorithm.name,
            styles['CustomTitle']
        ))
        
        # Subtítulo
        story.append(Paragraph(
            "Análisis de Complejidad Algorítmica",
            styles['CustomSubtitle']
        ))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Información del documento
        info_text = f"""
        <para alignment="center">
        <b>Generado:</b> {self.format_timestamp(data.timestamp)}<br/>
        <b>Versión del Analizador:</b> {data.analysis.analyzer_version}<br/>
        <b>Tiempo de Análisis:</b> {data.analysis.analysis_time:.3f}s
        </para>
        """
        story.append(Paragraph(info_text, styles['Normal']))
        
        return story
    
    def _generate_summary(self, data: ExportData, styles) -> List:
        """Genera sección de resumen"""
        story = []
        
        story.append(Paragraph("Resumen Ejecutivo", styles['SectionHeading']))
        story.append(Spacer(1, 0.1*inch))
        
        # Tabla de información general
        summary_data = [
            ['Atributo', 'Valor'],
            ['Nombre', data.algorithm.name],
            ['Lenguaje', data.algorithm.language],
            ['Categoría', data.algorithm.category or 'No especificada'],
        ]
        
        if data.algorithm.author:
            summary_data.append(['Autor', data.algorithm.author])
        
        if data.patterns:
            summary_data.append([
                'Patrón Principal',
                f"{data.patterns.primary_pattern} ({data.patterns.primary_confidence:.1%})"
            ])
        
        table = Table(summary_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(table)
        
        return story
    
    def _generate_code_section(self, data: ExportData, styles) -> List:
        """Genera sección de código"""
        story = []
        
        story.append(Paragraph("Código Fuente", styles['SectionHeading']))
        story.append(Spacer(1, 0.1*inch))
        
        # Dividir código en líneas y crear párrafos
        code_lines = data.algorithm.code.split('\n')
        for line in code_lines[:50]:  # Limitar a 50 líneas para el PDF
            if line.strip():
                # Escapar caracteres especiales
                line_escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"<font name='Courier' size='9'>{line_escaped}</font>", styles['Normal']))
        
        if len(code_lines) > 50:
            story.append(Paragraph(
                f"<i>... {len(code_lines) - 50} líneas adicionales omitidas ...</i>",
                styles['Normal']
            ))
        
        return story
    
    def _generate_complexity_section(self, data: ExportData, styles) -> List:
        """Genera sección de complejidad"""
        story = []
        
        story.append(Paragraph("Análisis de Complejidad", styles['SectionHeading']))
        story.append(Spacer(1, 0.1*inch))
        
        # Tabla de complejidades
        complexity_data = [
            ['Notación', 'Caso', 'Complejidad'],
            [
                'Big O (O)',
                'Peor caso',
                self.format_complexity(data.analysis.big_o)
            ],
            [
                'Omega (Ω)',
                'Mejor caso',
                self.format_complexity(data.analysis.omega)
            ],
        ]
        
        if data.analysis.theta:
            complexity_data.append([
                'Theta (Θ)',
                'Caso promedio',
                self.format_complexity(data.analysis.theta)
            ])
        
        if data.analysis.space_complexity:
            complexity_data.append([
                'Espacio',
                'Memoria',
                self.format_complexity(data.analysis.space_complexity)
            ])
        
        table = Table(complexity_data, colWidths=[1.5*inch, 2*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (2, 1), (2, -1), 'Courier-Bold'),
            ('FONTSIZE', (2, 1), (2, -1), 10),
        ]))
        
        story.append(table)
        
        # Ecuaciones de recurrencia
        if data.analysis.temporal_recurrence or data.analysis.spatial_recurrence:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Ecuaciones de Recurrencia", styles['Heading3']))
            
            if data.analysis.temporal_recurrence:
                story.append(Paragraph(
                    f"<b>Temporal:</b> <font name='Courier'>{data.analysis.temporal_recurrence}</font>",
                    styles['Normal']
                ))
            
            if data.analysis.spatial_recurrence:
                story.append(Paragraph(
                    f"<b>Espacial:</b> <font name='Courier'>{data.analysis.spatial_recurrence}</font>",
                    styles['Normal']
                ))
        
        return story
    
    def _generate_patterns_section(self, data: ExportData, styles) -> List:
        """Genera sección de patrones"""
        story = []
        
        story.append(Paragraph("Patrones Detectados", styles['SectionHeading']))
        story.append(Spacer(1, 0.1*inch))
        
        # Tabla de patrones
        pattern_data = [['Patrón', 'Confianza', 'Score']]
        
        for pattern in data.patterns.patterns_found[:10]:  # Top 10
            name = pattern.get("name", "Desconocido")
            confidence = pattern.get("confidence", 0)
            score = pattern.get("score", 0)
            
            pattern_data.append([
                name,
                f"{confidence:.1%}",
                f"{score:.2f}"
            ])
        
        table = Table(pattern_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#87CEEB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(table)
        
        return story
    
    def _generate_line_analysis_section(self, data: ExportData, styles) -> List:
        """Genera sección de análisis línea por línea"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("Análisis Línea por Línea", styles['SectionHeading']))
        story.append(Spacer(1, 0.1*inch))
        
        line_data = [['#', 'Código', 'Complejidad']]
        
        if isinstance(data.analysis.line_by_line, dict):
            for line_num, info in sorted(list(data.analysis.line_by_line.items())[:30]):  # Primeras 30
                code = info.get("code", "").strip()[:40]  # Limitar longitud
                complexity = info.get("complexity", "O(1)")
                
                line_data.append([
                    str(line_num),
                    code,
                    complexity
                ])
        
        table = Table(line_data, colWidths=[0.5*inch, 4*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFD93D')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('FONTNAME', (1, 1), (1, -1), 'Courier'),
            ('FONTNAME', (2, 1), (2, -1), 'Courier-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(table)
        
        return story

def export_to_pdf(
    data: ExportData,
    output_path: str = None
) -> ExportResult:
    """
    Helper para exportar a PDF rápidamente.
    
    Args:
        data: Datos a exportar
        output_path: Ruta de salida (opcional)
        
    Returns:
        ExportResult: Resultado de la exportación
    """
    from pathlib import Path
    from app.infrastructure.export.base_exporter import ExportConfig
    
    config = ExportConfig(
        format=ExportFormat.PDF,
        output_path=Path(output_path) if output_path else None
    )
    
    exporter = PDFExporter(config)
    return exporter.export(data)