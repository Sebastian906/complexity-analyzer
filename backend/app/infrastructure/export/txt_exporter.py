"""
Text Exporter - Exportador a formato texto plano

Exporta resultados de análisis a formato de texto plano (.txt)
ideal para logs, consola y salidas simples.
"""

import time
from typing import Any, Dict, List

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportData,
    ExportFormat,
    ExportResult
)


class TXTExporter(BaseExporter):
    """
    Exportador a formato texto plano.
    
    Genera documentos de texto simples y legibles con:
    - Separadores visuales
    - Estructura clara
    - Sin formato especial
    """
    
    def get_format(self) -> ExportFormat:
        """Retorna el formato TXT"""
        return ExportFormat.TXT
    
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos a formato texto plano.
        
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
            
            # Generar contenido de texto
            sections = []
            
            sections.append(self._generate_header(data))
            sections.append(self._generate_metadata(data))
            
            if self.config.include_code:
                sections.append(self._generate_code_section(data))
            
            sections.append(self._generate_complexity_section(data))
            
            if data.patterns:
                sections.append(self._generate_patterns_section(data))
            
            if data.analysis.line_by_line:
                sections.append(self._generate_line_analysis_section(data))
            
            # Filtrar secciones vacías
            sections = [s for s in sections if s.strip()]
            content = "\n\n".join(sections)
            
            # Guardar o retornar contenido
            if self.config.output_path:
                return self.save_to_file(content, time.time() - start_time)
            else:
                return self.create_result(
                    success=True,
                    content=content,
                    export_time=time.time() - start_time,
                    metadata={"sections_count": len(sections)}
                )
                
        except Exception as e:
            return self.create_result(
                success=False,
                errors=[str(e)],
                export_time=time.time() - start_time
            )
    
    def _generate_header(self, data: ExportData) -> str:
        """Genera encabezado del documento"""
        lines = []
        separator = "=" * 60
        
        lines.append(separator)
        if data.algorithm:
            lines.append(f"ANÁLISIS DE ALGORITMO: {data.algorithm.name}")
        else:
            lines.append("ANÁLISIS DE ALGORITMO")
        lines.append(separator)
        
        if data.algorithm and data.algorithm.description:
            lines.append("")
            lines.append(data.algorithm.description)
        
        return "\n".join(lines)
    
    def _generate_metadata(self, data: ExportData) -> str:
        """Genera sección de metadatos"""
        if not self.config.include_metadata:
            return ""
        
        lines = []
        lines.append("-" * 40)
        lines.append("INFORMACIÓN GENERAL")
        lines.append("-" * 40)
        
        if data.algorithm:
            lines.append(f"  Nombre:      {data.algorithm.name}")
            if data.algorithm.language:
                lines.append(f"  Lenguaje:    {data.algorithm.language}")
            if data.algorithm.category:
                lines.append(f"  Categoría:   {data.algorithm.category}")
        
        if data.analysis:
            lines.append(f"  ID Análisis: {data.analysis.id}")
            if data.analysis.analyzed_at:
                lines.append(f"  Fecha:       {data.analysis.analyzed_at}")
        
        return "\n".join(lines)
    
    def _generate_code_section(self, data: ExportData) -> str:
        """Genera sección de código fuente"""
        if not data.algorithm or not data.algorithm.code:
            return ""
        
        lines = []
        lines.append("-" * 40)
        lines.append("CÓDIGO FUENTE")
        lines.append("-" * 40)
        lines.append("")
        
        # Agregar números de línea
        code_lines = data.algorithm.code.split('\n')
        max_digits = len(str(len(code_lines)))
        
        for i, line in enumerate(code_lines, 1):
            lines.append(f"  {i:>{max_digits}} | {line}")
        
        return "\n".join(lines)
    
    def _generate_complexity_section(self, data: ExportData) -> str:
        """Genera sección de complejidad"""
        if not data.analysis:
            return ""
        
        lines = []
        lines.append("-" * 40)
        lines.append("ANÁLISIS DE COMPLEJIDAD")
        lines.append("-" * 40)
        
        # Complejidad temporal
        lines.append("")
        lines.append("  Complejidad Temporal:")
        lines.append(f"    - Big O (peor caso):    {data.analysis.time_complexity.big_o}")
        lines.append(f"    - Omega (mejor caso):   {data.analysis.time_complexity.omega}")
        lines.append(f"    - Theta (caso promedio): {data.analysis.time_complexity.theta}")
        lines.append(f"    - Confianza:            {data.analysis.time_complexity.confidence:.1%}")
        
        # Complejidad espacial
        lines.append("")
        lines.append("  Complejidad Espacial:")
        lines.append(f"    - Big O:     {data.analysis.space_complexity.big_o}")
        lines.append(f"    - Confianza: {data.analysis.space_complexity.confidence:.1%}")
        
        # Explicación si existe
        if data.analysis.time_complexity.explanation:
            lines.append("")
            lines.append("  Explicación:")
            # Wrap text for readability
            explanation = data.analysis.time_complexity.explanation
            wrapped = self._wrap_text(explanation, width=50, indent="    ")
            lines.append(wrapped)
        
        return "\n".join(lines)
    
    def _generate_patterns_section(self, data: ExportData) -> str:
        """Genera sección de patrones detectados"""
        if not data.patterns:
            return ""
        
        lines = []
        lines.append("-" * 40)
        lines.append("PATRONES DETECTADOS")
        lines.append("-" * 40)
        
        if hasattr(data.patterns, 'patterns') and data.patterns.patterns:
            for i, pattern in enumerate(data.patterns.patterns, 1):
                lines.append("")
                lines.append(f"  {i}. {pattern.name}")
                lines.append(f"     Tipo:      {pattern.pattern_type}")
                lines.append(f"     Confianza: {pattern.confidence:.1%}")
                if pattern.description:
                    wrapped = self._wrap_text(pattern.description, width=45, indent="     ")
                    lines.append(f"     Descripción:")
                    lines.append(wrapped)
        else:
            lines.append("  No se detectaron patrones específicos.")
        
        return "\n".join(lines)
    
    def _generate_line_analysis_section(self, data: ExportData) -> str:
        """Genera sección de análisis línea por línea"""
        if not data.analysis.line_by_line:
            return ""
        
        lines = []
        lines.append("-" * 40)
        lines.append("ANÁLISIS LÍNEA POR LÍNEA")
        lines.append("-" * 40)
        
        for line_info in data.analysis.line_by_line[:20]:  # Limitar a 20 líneas
            line_num = line_info.get('line_number', '?')
            complexity = line_info.get('complexity', 'O(1)')
            operations = line_info.get('operations', [])
            
            lines.append(f"  Línea {line_num}: {complexity}")
            if operations:
                ops_str = ", ".join(operations[:3])  # Máximo 3 operaciones
                lines.append(f"    Operaciones: {ops_str}")
        
        if len(data.analysis.line_by_line) > 20:
            lines.append(f"  ... y {len(data.analysis.line_by_line) - 20} líneas más")
        
        return "\n".join(lines)
    
    def _wrap_text(self, text: str, width: int = 60, indent: str = "") -> str:
        """Envuelve texto a un ancho máximo con indentación"""
        words = text.split()
        lines = []
        current_line = indent
        
        for word in words:
            if len(current_line) + len(word) + 1 <= width + len(indent):
                if current_line == indent:
                    current_line += word
                else:
                    current_line += " " + word
            else:
                if current_line != indent:
                    lines.append(current_line)
                current_line = indent + word
        
        if current_line != indent:
            lines.append(current_line)
        
        return "\n".join(lines)


def export_to_txt(
    algorithm,
    analysis,
    patterns=None,
    output_path: str = None,
    **kwargs
) -> ExportResult:
    """
    Función helper para exportar a texto plano.
    
    Args:
        algorithm: Algoritmo a exportar
        analysis: Resultado del análisis
        patterns: Patrones detectados (opcional)
        output_path: Ruta de salida (opcional)
        **kwargs: Opciones adicionales
        
    Returns:
        ExportResult: Resultado de la exportación
    """
    from pathlib import Path
    from app.infrastructure.export.base_exporter import ExportConfig
    
    data = ExportData(
        algorithm=algorithm,
        analysis=analysis,
        patterns=patterns
    )
    
    config = ExportConfig(
        format=ExportFormat.TXT,
        output_path=Path(output_path) if output_path else None,
        **kwargs
    )
    
    exporter = TXTExporter(config)
    return exporter.export(data)
