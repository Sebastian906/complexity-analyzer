"""
SVG Exporter - Exportador a formato SVG

Exporta visualizaciones a formato SVG escalable
ideal para documentación, presentaciones e impresión.
"""

import time
from typing import Dict, Any, List, Tuple
from xml.etree import ElementTree as ET

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportData,
    ExportFormat,
    ExportResult
)

class SVGExporter(BaseExporter):
    """
    Exportador a formato SVG.
    
    Genera gráficos SVG vectoriales de:
    - Árboles de recursión
    - Grafos de complejidad
    - Diagramas de patrones
    """
    
    # Constantes de diseño
    NODE_WIDTH = 120
    NODE_HEIGHT = 50
    LEVEL_HEIGHT = 100
    SIBLING_SPACING = 20
    
    def get_format(self) -> ExportFormat:
        """Retorna el formato SVG"""
        return ExportFormat.SVG
    
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos a formato SVG.
        
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
            
            # Generar múltiples SVGs
            svg_files = {}
            
            if data.visualizations:
                # Árbol de recursión
                if "recursion_tree" in data.visualizations:
                    tree_svg = self._generate_recursion_tree_svg(
                        data.visualizations["recursion_tree"],
                        data.algorithm.name
                    )
                    svg_files["recursion_tree"] = tree_svg
            
            # Diagrama de complejidad (siempre)
            complexity_svg = self._generate_complexity_chart_svg(data)
            svg_files["complexity"] = complexity_svg
            
            # Diagrama de patrones
            if data.patterns and data.patterns.patterns_found:
                patterns_svg = self._generate_patterns_chart_svg(data)
                svg_files["patterns"] = patterns_svg
            
            # Guardar archivos
            results = []
            total_size = 0
            
            for name, svg_element in svg_files.items():
                suffix = f"_{name}" if name != "complexity" else ""
                output_path = self.prepare_output_path(data, suffix=suffix)
                
                svg_string = ET.tostring(svg_element, encoding='unicode', method='xml')
                
                file_size = self.save_to_file(svg_string, output_path)
                total_size += file_size
                results.append(str(output_path))
            
            export_time = time.time() - start_time
            
            self.logger.info(f"Exportación SVG completada: {len(svg_files)} gráficos en {export_time:.3f}s")
            
            return self.create_result(
                success=True,
                output_path=None,  # Múltiples archivos
                file_size=total_size,
                export_time=export_time,
                files_generated=results,
                svg_count=len(svg_files)
            )
            
        except Exception as e:
            self.logger.error(f"Error en exportación SVG: {str(e)}")
            return self.create_result(
                success=False,
                errors=[str(e)],
                export_time=time.time() - start_time
            )
    
    def _generate_recursion_tree_svg(
        self,
        tree: Dict[str, Any],
        algorithm_name: str
    ) -> ET.Element:
        """
        Genera SVG del árbol de recursión.
        
        Args:
            tree: Datos del árbol
            algorithm_name: Nombre del algoritmo
            
        Returns:
            ET.Element: Elemento SVG
        """
        # Calcular dimensiones del árbol
        width, height = self._calculate_tree_dimensions(tree)
        
        # Crear elemento SVG raíz
        svg = ET.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': str(width + 100),
            'height': str(height + 100),
            'viewBox': f'0 0 {width + 100} {height + 100}'
        })
        
        # Título
        title = ET.SubElement(svg, 'title')
        title.text = f"Árbol de Recursión - {algorithm_name}"
        
        # Grupo principal
        g = ET.SubElement(svg, 'g', {'transform': 'translate(50, 50)'})
        
        # Renderizar árbol
        self._render_tree_node(g, tree, width // 2, 0, width // 4)
        
        return svg
    
    def _calculate_tree_dimensions(self, tree: Dict[str, Any]) -> Tuple[int, int]:
        """Calcula dimensiones necesarias para el árbol"""
        def count_leaves(node: Dict[str, Any]) -> int:
            children = node.get("children", [])
            if not children:
                return 1
            return sum(count_leaves(child) for child in children)
        
        def get_depth(node: Dict[str, Any]) -> int:
            children = node.get("children", [])
            if not children:
                return 1
            return 1 + max(get_depth(child) for child in children)
        
        leaves = count_leaves(tree)
        depth = get_depth(tree)
        
        width = max(800, leaves * (self.NODE_WIDTH + self.SIBLING_SPACING))
        height = depth * self.LEVEL_HEIGHT + 50
        
        return width, height
    
    def _render_tree_node(
        self,
        parent: ET.Element,
        node: Dict[str, Any],
        x: float,
        y: float,
        x_offset: float
    ) -> None:
        """
        Renderiza un nodo del árbol recursivamente.
        
        Args:
            parent: Elemento padre SVG
            node: Datos del nodo
            x, y: Posición del nodo
            x_offset: Offset horizontal para hijos
        """
        label = node.get("label", "?")
        is_base = node.get("metadata", {}).get("is_base_case", False)
        node_type = node.get("type", "internal")
        
        # Color según tipo
        if is_base:
            fill = "#90EE90"
            stroke = "#228B22"
        elif node_type == "call":
            fill = "#87CEEB"
            stroke = "#4682B4"
        else:
            fill = "#FFE4B5"
            stroke = "#DAA520"
        
        # Rectángulo del nodo
        ET.SubElement(parent, 'rect', {
            'x': str(x - self.NODE_WIDTH // 2),
            'y': str(y),
            'width': str(self.NODE_WIDTH),
            'height': str(self.NODE_HEIGHT),
            'fill': fill,
            'stroke': stroke,
            'stroke-width': '2',
            'rx': '5'
        })
        
        # Texto del nodo
        text = ET.SubElement(parent, 'text', {
            'x': str(x),
            'y': str(y + self.NODE_HEIGHT // 2 + 5),
            'text-anchor': 'middle',
            'font-family': 'Arial',
            'font-size': '14',
            'fill': '#000'
        })
        text.text = label
        
        # Renderizar hijos
        children = node.get("children", [])
        if children:
            child_y = y + self.LEVEL_HEIGHT
            num_children = len(children)
            
            # Calcular posiciones de hijos
            if num_children == 1:
                child_x = x
            else:
                start_x = x - (num_children - 1) * x_offset / 2
                child_x = start_x
            
            for i, child in enumerate(children):
                if num_children > 1:
                    child_x = x - (num_children - 1) * x_offset / 2 + i * x_offset
                else:
                    child_x = x
                
                # Línea al hijo
                ET.SubElement(parent, 'line', {
                    'x1': str(x),
                    'y1': str(y + self.NODE_HEIGHT),
                    'x2': str(child_x),
                    'y2': str(child_y),
                    'stroke': '#666',
                    'stroke-width': '2'
                })
                
                # Renderizar hijo recursivamente
                new_offset = x_offset / 2 if num_children > 1 else x_offset
                self._render_tree_node(parent, child, child_x, child_y, new_offset)
    
    def _generate_complexity_chart_svg(self, data: ExportData) -> ET.Element:
        """
        Genera gráfico de barras de complejidad.
        
        Args:
            data: Datos del análisis
            
        Returns:
            ET.Element: Elemento SVG
        """
        width, height = 600, 400
        
        svg = ET.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': str(width),
            'height': str(height),
            'viewBox': f'0 0 {width} {height}'
        })
        
        # Título
        title = ET.SubElement(svg, 'title')
        title.text = f"Análisis de Complejidad - {data.algorithm.name}"
        
        # Fondo
        ET.SubElement(svg, 'rect', {
            'width': str(width),
            'height': str(height),
            'fill': '#f9f9f9'
        })
        
        # Título del gráfico
        title_text = ET.SubElement(svg, 'text', {
            'x': str(width // 2),
            'y': '30',
            'text-anchor': 'middle',
            'font-family': 'Arial',
            'font-size': '20',
            'font-weight': 'bold'
        })
        title_text.text = f"Complejidad: {data.algorithm.name}"
        
        # Datos de complejidad
        complexities = [
            ("Big O", data.analysis.big_o, "#FF6B6B"),
            ("Omega", data.analysis.omega, "#90EE90"),
        ]
        
        if data.analysis.theta:
            complexities.append(("Theta", data.analysis.theta, "#FFD93D"))
        
        if data.analysis.space_complexity:
            complexities.append(("Espacio", data.analysis.space_complexity, "#B19CD9"))
        
        # Renderizar barras
        bar_width = 80
        spacing = 120
        start_x = (width - len(complexities) * spacing) // 2
        
        for i, (label, complexity, color) in enumerate(complexities):
            x = start_x + i * spacing
            y = height - 150
            
            # Barra
            ET.SubElement(svg, 'rect', {
                'x': str(x),
                'y': str(y),
                'width': str(bar_width),
                'height': '100',
                'fill': color,
                'stroke': '#333',
                'stroke-width': '2',
                'rx': '5'
            })
            
            # Etiqueta
            label_text = ET.SubElement(svg, 'text', {
                'x': str(x + bar_width // 2),
                'y': str(y - 10),
                'text-anchor': 'middle',
                'font-family': 'Arial',
                'font-size': '14',
                'font-weight': 'bold'
            })
            label_text.text = label
            
            # Complejidad
            comp_text = ET.SubElement(svg, 'text', {
                'x': str(x + bar_width // 2),
                'y': str(y + 55),
                'text-anchor': 'middle',
                'font-family': 'Arial',
                'font-size': '16',
                'fill': '#000'
            })
            comp_text.text = self.format_complexity(complexity)
        
        return svg
    
    def _generate_patterns_chart_svg(self, data: ExportData) -> ET.Element:
        """
        Genera gráfico de patrones detectados.
        
        Args:
            data: Datos del análisis
            
        Returns:
            ET.Element: Elemento SVG
        """
        width, height = 500, 400
        
        svg = ET.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': str(width),
            'height': str(height),
            'viewBox': f'0 0 {width} {height}'
        })
        
        # Título
        title = ET.SubElement(svg, 'title')
        title.text = f"Patrones Detectados - {data.algorithm.name}"
        
        # Fondo
        ET.SubElement(svg, 'rect', {
            'width': str(width),
            'height': str(height),
            'fill': '#f9f9f9'
        })
        
        # Título del gráfico
        title_text = ET.SubElement(svg, 'text', {
            'x': str(width // 2),
            'y': '30',
            'text-anchor': 'middle',
            'font-family': 'Arial',
            'font-size': '18',
            'font-weight': 'bold'
        })
        title_text.text = "Patrones Detectados"
        
        # Top 5 patrones
        patterns = data.patterns.patterns_found[:5]
        
        bar_height = 40
        bar_spacing = 60
        start_y = 80
        max_bar_width = 350
        
        for i, pattern in enumerate(patterns):
            name = pattern.get("name", "Desconocido")
            confidence = pattern.get("confidence", 0)
            
            y = start_y + i * bar_spacing
            bar_width = confidence * max_bar_width
            
            # Barra de confianza
            ET.SubElement(svg, 'rect', {
                'x': '120',
                'y': str(y),
                'width': str(bar_width),
                'height': str(bar_height),
                'fill': '#87CEEB',
                'stroke': '#4682B4',
                'stroke-width': '1',
                'rx': '3'
            })
            
            # Nombre del patrón
            name_text = ET.SubElement(svg, 'text', {
                'x': '10',
                'y': str(y + bar_height // 2 + 5),
                'font-family': 'Arial',
                'font-size': '12',
                'fill': '#333'
            })
            name_text.text = name[:15] + "..." if len(name) > 15 else name
            
            # Porcentaje
            pct_text = ET.SubElement(svg, 'text', {
                'x': str(130 + bar_width),
                'y': str(y + bar_height // 2 + 5),
                'font-family': 'Arial',
                'font-size': '12',
                'font-weight': 'bold',
                'fill': '#333'
            })
            pct_text.text = f"{confidence:.1%}"
        
        return svg

def export_to_svg(
    data: ExportData,
    output_path: str = None
) -> ExportResult:
    """
    Helper para exportar a SVG rápidamente.
    
    Args:
        data: Datos a exportar
        output_path: Ruta de salida (opcional)
        
    Returns:
        ExportResult: Resultado de la exportación
    """
    from pathlib import Path
    from app.infrastructure.export.base_exporter import ExportConfig
    
    config = ExportConfig(
        format=ExportFormat.SVG,
        output_path=Path(output_path) if output_path else None
    )
    
    exporter = SVGExporter(config)
    return exporter.export(data)