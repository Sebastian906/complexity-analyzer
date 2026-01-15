"""
DOT Exporter - Exportador a formato DOT (Graphviz)

Exporta árboles de recursión y grafos de ejecución
al formato DOT para renderizado con Graphviz.
"""

import time
from typing import Dict, Any, List, Optional

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportData,
    ExportFormat,
    ExportResult
)

class DOTExporter(BaseExporter):
    """
    Exportador a formato DOT (Graphviz).
    
    Genera archivos .dot para visualización de:
    - Árboles de recursión
    - Grafos de flujo de ejecución
    - Estructuras de datos
    """
    
    def get_format(self) -> ExportFormat:
        """Retorna el formato DOT"""
        return ExportFormat.DOT
    
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos a formato DOT.
        
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
            
            # Generar múltiples archivos DOT si hay múltiples visualizaciones
            dot_files = {}
            
            if data.visualizations:
                # Árbol de recursión
                if "recursion_tree" in data.visualizations:
                    tree_dot = self._generate_recursion_tree_dot(
                        data.visualizations["recursion_tree"],
                        data.algorithm.name
                    )
                    dot_files["recursion_tree"] = tree_dot
                
                # Grafo de ejecución
                if "execution_flow" in data.visualizations:
                    flow_dot = self._generate_execution_flow_dot(
                        data.visualizations["execution_flow"],
                        data.algorithm.name
                    )
                    dot_files["execution_flow"] = flow_dot
            
            # Si no hay visualizaciones, generar un grafo básico
            if not dot_files:
                basic_dot = self._generate_basic_complexity_graph(data)
                dot_files["complexity"] = basic_dot
            
            # Guardar archivos
            results = []
            total_size = 0
            
            for name, content in dot_files.items():
                suffix = f"_{name}" if name != "complexity" else ""
                output_path = self.prepare_output_path(data, suffix=suffix)
                
                file_size = self.save_to_file(content, output_path)
                total_size += file_size
                results.append(str(output_path))
            
            export_time = time.time() - start_time
            
            self.logger.info(f"Exportación DOT completada: {len(dot_files)} archivos en {export_time:.3f}s")
            
            return self.create_result(
                success=True,
                output_path=None,  # Múltiples archivos
                file_size=total_size,
                export_time=export_time,
                files_generated=results,
                graphs_count=len(dot_files)
            )
            
        except Exception as e:
            self.logger.error(f"Error en exportación DOT: {str(e)}")
            return self.create_result(
                success=False,
                errors=[str(e)],
                export_time=time.time() - start_time
            )
    
    def _generate_recursion_tree_dot(
        self,
        tree: Dict[str, Any],
        algorithm_name: str
    ) -> str:
        """
        Genera código DOT para árbol de recursión.
        
        Args:
            tree: Datos del árbol
            algorithm_name: Nombre del algoritmo
            
        Returns:
            str: Código DOT
        """
        lines = [
            "digraph RecursionTree {",
            "    // Configuración general",
            "    rankdir=TB;",
            "    node [shape=box, style=rounded, fontname=\"Arial\"];",
            "    edge [fontname=\"Arial\", fontsize=10];",
            "",
            f"    // Árbol de recursión: {algorithm_name}",
            f"    label=\"Árbol de Recursión - {algorithm_name}\";",
            "    labelloc=t;",
            "    fontsize=16;",
            ""
        ]
        
        # Generar nodos y aristas
        node_definitions = []
        edge_definitions = []
        
        def process_node(node: Dict[str, Any], parent_id: Optional[str] = None):
            node_id = node.get("id", "unknown")
            label = node.get("label", "?")
            node_type = node.get("type", "internal")
            is_base = node.get("metadata", {}).get("is_base_case", False)
            
            # Estilo del nodo según tipo
            if is_base:
                style = 'filled, fillcolor="#90EE90"'  # Verde claro
            elif node_type == "call":
                style = 'filled, fillcolor="#87CEEB"'  # Azul cielo
            else:
                style = 'filled, fillcolor="#FFE4B5"'  # Beige
            
            node_definitions.append(
                f'    {node_id} [label="{label}", {style}];'
            )
            
            # Crear arista al padre
            if parent_id:
                edge_definitions.append(f"    {parent_id} -> {node_id};")
            
            # Procesar hijos
            for child in node.get("children", []):
                process_node(child, node_id)
        
        # Procesar desde la raíz
        if isinstance(tree, dict):
            process_node(tree)
        
        # Agregar definiciones al código
        lines.append("    // Nodos")
        lines.extend(node_definitions)
        lines.append("")
        lines.append("    // Aristas")
        lines.extend(edge_definitions)
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_execution_flow_dot(
        self,
        flow: Dict[str, Any],
        algorithm_name: str
    ) -> str:
        """
        Genera código DOT para grafo de flujo de ejecución.
        
        Args:
            flow: Datos del grafo de flujo
            algorithm_name: Nombre del algoritmo
            
        Returns:
            str: Código DOT
        """
        lines = [
            "digraph ExecutionFlow {",
            "    // Configuración general",
            "    rankdir=TB;",
            "    node [fontname=\"Arial\"];",
            "    edge [fontname=\"Arial\"];",
            "",
            f"    // Flujo de ejecución: {algorithm_name}",
            f"    label=\"Flujo de Ejecución - {algorithm_name}\";",
            "    labelloc=t;",
            "    fontsize=16;",
            ""
        ]
        
        # Procesar nodos del flujo
        nodes = flow.get("nodes", [])
        edges = flow.get("edges", [])
        
        # Definir nodos con estilos según tipo
        lines.append("    // Nodos")
        for node in nodes:
            node_id = node.get("id", "unknown")
            label = node.get("label", "?")
            node_type = node.get("type", "operation")
            
            # Estilos según tipo de nodo
            if node_type == "decision":
                shape = "diamond"
                color = "#FFD700"  # Dorado
            elif node_type == "loop":
                shape = "box, style=rounded"
                color = "#FFA500"  # Naranja
            elif node_type == "call":
                shape = "ellipse"
                color = "#87CEEB"  # Azul
            else:
                shape = "box"
                color = "#E0E0E0"  # Gris claro
            
            lines.append(
                f'    {node_id} [label="{label}", shape={shape}, '
                f'style=filled, fillcolor="{color}"];'
            )
        
        # Definir aristas
        lines.append("")
        lines.append("    // Aristas")
        for edge in edges:
            from_node = edge.get("from", "?")
            to_node = edge.get("to", "?")
            label = edge.get("label", "")
            
            if label:
                lines.append(f'    {from_node} -> {to_node} [label="{label}"];')
            else:
                lines.append(f"    {from_node} -> {to_node};")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_basic_complexity_graph(self, data: ExportData) -> str:
        """
        Genera un grafo básico mostrando complejidades.
        
        Args:
            data: Datos del análisis
            
        Returns:
            str: Código DOT
        """
        lines = [
            "digraph ComplexityGraph {",
            "    // Configuración general",
            "    rankdir=TB;",
            "    node [shape=box, style=rounded, fontname=\"Arial\"];",
            "",
            f"    // Complejidad: {data.algorithm.name}",
            f"    label=\"Análisis de Complejidad - {data.algorithm.name}\";",
            "    labelloc=t;",
            "    fontsize=16;",
            "",
            "    // Nodos de complejidad",
            f'    algorithm [label="{data.algorithm.name}", shape=ellipse, '
            'style=filled, fillcolor="#87CEEB"];',
            ""
        ]
        
        # Nodos de complejidad
        complexities = [
            ("big_o", data.analysis.big_o, "Peor caso", "#FF6B6B"),
            ("omega", data.analysis.omega, "Mejor caso", "#90EE90"),
        ]
        
        if data.analysis.theta:
            complexities.append(
                ("theta", data.analysis.theta, "Caso promedio", "#FFD93D")
            )
        
        for node_id, complexity, label, color in complexities:
            lines.append(
                f'    {node_id} [label="{label}\\n{complexity}", '
                f'style=filled, fillcolor="{color}"];'
            )
            lines.append(f"    algorithm -> {node_id};")
        
        # Complejidad espacial
        if data.analysis.space_complexity:
            lines.append("")
            lines.append(
                f'    space [label="Espacio\\n{data.analysis.space_complexity}", '
                'style=filled, fillcolor="#B19CD9"];'
            )
            lines.append("    algorithm -> space;")
        
        lines.append("}")
        
        return "\n".join(lines)

def export_to_dot(
    data: ExportData,
    output_path: str = None
) -> ExportResult:
    """
    Helper para exportar a DOT rápidamente.
    
    Args:
        data: Datos a exportar
        output_path: Ruta de salida (opcional)
        
    Returns:
        ExportResult: Resultado de la exportación
    """
    from pathlib import Path
    from app.infrastructure.export.base_exporter import ExportConfig
    
    config = ExportConfig(
        format=ExportFormat.DOT,
        output_path=Path(output_path) if output_path else None
    )
    
    exporter = DOTExporter(config)
    return exporter.export(data)