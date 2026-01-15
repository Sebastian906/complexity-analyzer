"""
Markdown Exporter - Exportador a formato Markdown

Exporta resultados de análisis a formato Markdown
ideal para documentación, GitHub, y sitios estáticos.
"""

import time
from typing import List, Dict, Any

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportData,
    ExportFormat,
    ExportResult
)

class MarkdownExporter(BaseExporter):
    """
    Exportador a formato Markdown.
    
    Genera documentos Markdown bien estructurados con:
    - Encabezados jerárquicos
    - Bloques de código
    - Tablas
    - Listas
    - Enlaces
    """
    
    def get_format(self) -> ExportFormat:
        """Retorna el formato Markdown"""
        return ExportFormat.MARKDOWN
    
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos a formato Markdown.
        
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
            
            # Generar contenido Markdown
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
            
            if self.config.include_visualizations and data.visualizations:
                sections.append(self._generate_visualizations_section(data))
            
            if self.config.include_statistics:
                sections.append(self._generate_statistics_section(data))
            
            sections.append(self._generate_footer(data))
            
            # Unir secciones
            markdown_content = "\n\n".join(filter(None, sections))
            
            # Guardar o retornar
            output_path = None
            file_size = None
            
            if self.config.output_path or self.config.custom_options.get("save_to_file", True):
                output_path = self.prepare_output_path(data)
                file_size = self.save_to_file(markdown_content, output_path)
            
            export_time = time.time() - start_time
            
            self.logger.info(f"Exportación Markdown completada en {export_time:.3f}s")
            
            return self.create_result(
                success=True,
                output_path=output_path,
                content=markdown_content if not output_path else None,
                file_size=file_size,
                export_time=export_time,
                sections_count=len(sections),
                lines_count=markdown_content.count('\n')
            )
            
        except Exception as e:
            self.logger.error(f"Error en exportación Markdown: {str(e)}")
            return self.create_result(
                success=False,
                errors=[str(e)],
                export_time=time.time() - start_time
            )
    
    def _generate_header(self, data: ExportData) -> str:
        """Genera el encabezado del documento"""
        lines = [
            f"# {data.algorithm.name}",
            "",
            f"> Análisis de Complejidad Algorítmica",
            f"> Generado: {self.format_timestamp(data.timestamp)}",
            ""
        ]
        
        if data.algorithm.description:
            lines.extend([
                "## Descripción",
                "",
                data.algorithm.description,
                ""
            ])
        
        return "\n".join(lines)
    
    def _generate_metadata(self, data: ExportData) -> str:
        """Genera la sección de metadatos"""
        lines = [
            "## Información General",
            "",
            "| Campo | Valor |",
            "|-------|-------|",
            f"| **Nombre** | `{data.algorithm.name}` |",
            f"| **Lenguaje** | {data.algorithm.language} |",
        ]
        
        if data.algorithm.category:
            lines.append(f"| **Categoría** | {data.algorithm.category} |")
        
        if data.algorithm.author:
            lines.append(f"| **Autor** | {data.algorithm.author} |")
        
        if data.algorithm.tags:
            tags = ", ".join(f"`{tag}`" for tag in data.algorithm.tags)
            lines.append(f"| **Tags** | {tags} |")
        
        return "\n".join(lines)
    
    def _generate_code_section(self, data: ExportData) -> str:
        """Genera la sección de código"""
        lines = [
            "## Código Fuente",
            "",
            f"```{data.algorithm.language}",
            data.algorithm.code.strip(),
            "```",
        ]
        
        return "\n".join(lines)
    
    def _generate_complexity_section(self, data: ExportData) -> str:
        """Genera la sección de complejidad"""
        lines = [
            "## Análisis de Complejidad",
            "",
            "### Complejidad Temporal",
            "",
            "| Notación | Complejidad |",
            "|----------|-------------|",
            f"| **Big O (Peor caso)** | `{self.format_complexity(data.analysis.big_o)}` |",
            f"| **Omega (Mejor caso)** | `{self.format_complexity(data.analysis.omega)}` |",
        ]
        
        if data.analysis.theta:
            lines.append(f"| **Theta (Caso promedio)** | `{self.format_complexity(data.analysis.theta)}` |")
        
        # Ecuación de recurrencia temporal
        if data.analysis.temporal_recurrence:
            lines.extend([
                "",
                "#### Ecuación de Recurrencia",
                "",
                f"```",
                data.analysis.temporal_recurrence,
                "```",
            ])
        
        # Complejidad espacial
        if data.analysis.space_complexity:
            lines.extend([
                "",
                "### Complejidad Espacial",
                "",
                f"**Complejidad:** `{self.format_complexity(data.analysis.space_complexity)}`",
            ])
            
            if data.analysis.spatial_recurrence:
                lines.extend([
                    "",
                    "#### Ecuación de Recurrencia Espacial",
                    "",
                    f"```",
                    data.analysis.spatial_recurrence,
                    "```",
                ])
        
        return "\n".join(lines)
    
    def _generate_patterns_section(self, data: ExportData) -> str:
        """Genera la sección de patrones"""
        if not data.patterns:
            return ""
        
        lines = [
            "## Patrones Detectados",
            "",
            "### Patrón Principal",
            "",
            f"- **Patrón:** {data.patterns.primary_pattern}",
            f"- **Confianza:** {data.patterns.primary_confidence:.2%}",
            ""
        ]
        
        # Todos los patrones
        if data.patterns.patterns_found:
            lines.extend([
                "### Todos los Patrones",
                ""
            ])
            
            for pattern in data.patterns.patterns_found:
                pattern_name = pattern.get("name", "Desconocido")
                confidence = pattern.get("confidence", 0)
                score = pattern.get("score", 0)
                
                lines.append(f"- **{pattern_name}** (Confianza: {confidence:.2%}, Score: {score:.2f})")
                evidence = pattern.get("evidence", [])
                if not isinstance(evidence, (list, tuple)):
                    evidence = [evidence]
                if evidence:
                    lines.append(f"  - Evidencia: {len(evidence)} características detectadas")
        
        # Estructuras de datos
        if data.patterns.structures_found:
            lines.extend([
                "",
                "### Estructuras de Datos",
                ""
            ])
            
            for structure in data.patterns.structures_found:
                struct_name = structure.get("name", "Desconocida")
                confidence = structure.get("confidence", 0)
                operations = structure.get("operations", [])
                
                lines.append(f"- **{struct_name}** (Confianza: {confidence:.2%})")
                
                if operations:
                    lines.append(f"  - Operaciones: {', '.join(operations)}")
        
        return "\n".join(lines)
    
    def _generate_line_analysis_section(self, data: ExportData) -> str:
        """Genera la sección de análisis línea por línea"""
        if not data.analysis.line_by_line:
            return ""

        lines = [
            "## Análisis Línea por Línea",
            "",
            "| Línea | Código | Complejidad | Ejecuciones |",
            "|-------|--------|-------------|-------------|"
        ]

        line_data = data.analysis.line_by_line

        # CORRECCIÓN: Verificar el tipo de line_by_line
        if isinstance(line_data, dict):
            # Ordenar por número de línea
            sorted_items = sorted(line_data.items(), key=lambda x: int(x[0]) if isinstance(x[0], (int, str)) and str(x[0]).isdigit() else 0)

            for line_num, info in sorted_items:
                # Verificar que info sea un dict
                if not isinstance(info, dict):
                    continue

                code = info.get("code", "").strip()[:50]  # Limitar longitud
                complexity = info.get("complexity", "O(1)")
                executions = info.get("executions", "1")

                # Escapar caracteres especiales en markdown
                code = code.replace("|", "\\|")

                lines.append(f"| {line_num} | `{code}` | `{complexity}` | {executions} |")
        elif isinstance(line_data, list):
            # Si es una lista, iterar directamente
            for i, info in enumerate(line_data, 1):
                if not isinstance(info, dict):
                    continue

                line_num = info.get("line", i)
                code = info.get("code", "").strip()[:50]
                complexity = info.get("complexity", "O(1)")
                executions = info.get("executions", "1")

                code = code.replace("|", "\\|")
                lines.append(f"| {line_num} | `{code}` | `{complexity}` | {executions} |")

        return "\n".join(lines)
    
    def _generate_visualizations_section(self, data: ExportData) -> str:
        """Genera la sección de visualizaciones"""
        if not data.visualizations:
            return ""
        
        lines = [
            "## Visualizaciones",
            ""
        ]
        
        # Árbol de recursión
        if "recursion_tree" in data.visualizations:
            tree = data.visualizations["recursion_tree"]
            lines.extend([
                "### Árbol de Recursión",
                "",
                "```",
                self._format_tree_ascii(tree) if isinstance(tree, dict) else str(tree),
                "```",
                ""
            ])
        
        # Grafo de ejecución
        if "execution_flow" in data.visualizations:
            lines.append("### Grafo de Flujo de Ejecución")
            lines.append("")
            lines.append("*Ver archivo de visualización adjunto*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_statistics_section(self, data: ExportData) -> str:
        """Genera la sección de estadísticas"""
        lines = [
            "## Estadísticas",
            "",
            "| Métrica | Valor |",
            "|---------|-------|",
            f"| **Tiempo de análisis** | {data.analysis.analysis_time:.3f}s |",
            f"| **Versión del analizador** | {data.analysis.analyzer_version} |",
        ]
        
        if data.patterns:
            lines.append(f"| **Tiempo de detección** | {data.patterns.detection_time:.3f}s |")
        
        return "\n".join(lines)
    
    def _generate_footer(self, data: ExportData) -> str:
        """Genera el pie del documento"""
        lines = [
            "---",
            "",
            f"*Documento generado por Complexity Analyzer v{data.analysis.analyzer_version}*",
            f"*Fecha: {self.format_timestamp(data.timestamp)}*"
        ]
        
        return "\n".join(lines)
    
    def _format_tree_ascii(self, tree: Dict[str, Any]) -> str:
        """Formatea un árbol como ASCII art"""
        # Simplificado - en una implementación real sería más complejo
        if not tree:
            return "Árbol vacío"
        
        def format_node(node: Dict[str, Any], prefix: str = "", is_last: bool = True) -> List[str]:
            lines = []
            connector = "└── " if is_last else "├── "
            label = node.get("label", "?")
            lines.append(f"{prefix}{connector if prefix else ''}{label}")
            
            children = node.get("children", [])
            child_prefix = prefix + ("    " if is_last else "│   ")
            
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                lines.extend(format_node(child, child_prefix, is_last_child))
            
            return lines
        
        return "\n".join(format_node(tree))

def export_to_markdown(
    data: ExportData,
    output_path: str = None
) -> ExportResult:
    """
    Helper para exportar a Markdown rápidamente.
    
    Args:
        data: Datos a exportar
        output_path: Ruta de salida (opcional)
        
    Returns:
        ExportResult: Resultado de la exportación
    """
    from pathlib import Path
    from app.infrastructure.export.base_exporter import ExportConfig
    
    config = ExportConfig(
        format=ExportFormat.MARKDOWN,
        output_path=Path(output_path) if output_path else None
    )
    
    exporter = MarkdownExporter(config)
    return exporter.export(data)