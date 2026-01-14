"""
Mermaid Exporter - Exportador a formato Mermaid

Exporta diagramas en sintaxis Mermaid para uso en:
- Markdown (GitHub, GitLab)
- Documentación (Docusaurus, MkDocs)
- Presentaciones
"""

import time
from typing import Dict, Any, List, Optional

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportData,
    ExportFormat,
    ExportResult
)

class MermaidExporter(BaseExporter):
    """
    Exportador a formato Mermaid.
    
    Genera diagramas Mermaid para:
    - Árboles de recursión (graph)
    - Flujos de ejecución (flowchart)
    - Diagramas de complejidad (graph)
    """
    
    def get_format(self) -> ExportFormat:
        """Retorna el formato Mermaid"""
        return ExportFormat.MERMAID
    
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos a formato Mermaid.
        
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
            
            # Generar múltiples diagramas Mermaid
            mermaid_files = {}
            
            if data.visualizations:
                # Árbol de recursión
                if "recursion_tree" in data.visualizations:
                    tree_mermaid = self._generate_recursion_tree_mermaid(
                        data.visualizations["recursion_tree"],
                        data.algorithm.name
                    )
                    mermaid_files["recursion_tree"] = tree_mermaid
                
                # Grafo de ejecución
                if "execution_flow" in data.visualizations:
                    flow_mermaid = self._generate_execution_flow_mermaid(
                        data.visualizations["execution_flow"],
                        data.algorithm.name
                    )
                    mermaid_files["execution_flow"] = flow_mermaid
            
            # Diagrama de complejidad
            complexity_mermaid = self._generate_complexity_diagram(data)
            mermaid_files["complexity"] = complexity_mermaid
            
            # Si hay patrones, generar diagrama
            if data.patterns and data.patterns.patterns_found:
                patterns_mermaid = self._generate_patterns_diagram(data)
                mermaid_files["patterns"] = patterns_mermaid
            
            # Guardar archivos
            results = []
            total_size = 0
            
            for name, content in mermaid_files.items():
                if self.config.output_path:
                    base_path = self.prepare_output_path(data)
                    output_path = base_path.parent / f"{base_path.stem}_{name}.mmd"
                else:
                    output_path = self.prepare_output_path(data)
                    output_path = output_path.parent / f"{data.algorithm.name}_{name}.mmd"
                
                file_size = self.save_to_file(content, output_path)
                total_size += file_size
                results.append(str(output_path))
            
            export_time = time.time() - start_time
            
            self.logger.info(f"Exportación Mermaid completada: {len(mermaid_files)} diagramas en {export_time:.3f}s")
            
            return self.create_result(
                success=True,
                output_path=None,  # Múltiples archivos
                file_size=total_size,
                export_time=export_time,
                files_generated=results,
                diagrams_count=len(mermaid_files)
            )
            
        except Exception as e:
            self.logger.error(f"Error en exportación Mermaid: {str(e)}")
            return self.create_result(
                success=False,
                errors=[str(e)],
                export_time=time.time() - start_time
            )
    
    def _sanitize_id(self, text: str) -> str:
        """Sanitiza IDs para Mermaid (sin espacios ni caracteres especiales)"""
        return text.replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "")
    
    def _generate_recursion_tree_mermaid(
        self,
        tree: Dict[str, Any],
        algorithm_name: str
    ) -> str:
        """
        Genera diagrama Mermaid para árbol de recursión.
        
        Args:
            tree: Datos del árbol
            algorithm_name: Nombre del algoritmo
            
        Returns:
            str: Código Mermaid
        """
        lines = [
            "```mermaid",
            "graph TD",
            f"    %% Árbol de Recursión: {algorithm_name}",
            ""
        ]
        
        def process_node(node: Dict[str, Any], parent_id: Optional[str] = None):
            node_id = self._sanitize_id(node.get("id", "unknown"))
            label = node.get("label", "?")
            node_type = node.get("type", "internal")
            is_base = node.get("metadata", {}).get("is_base_case", False)
            
            # Estilo del nodo según tipo
            if is_base:
                # Nodo base case - rectángulo redondeado verde
                lines.append(f'    {node_id}["{label}"]')
                lines.append(f"    style {node_id} fill:#90EE90,stroke:#228B22")
            elif node_type == "call":
                # Nodo de llamada - rectángulo azul
                lines.append(f'    {node_id}["{label}"]')
                lines.append(f"    style {node_id} fill:#87CEEB,stroke:#4682B4")
            else:
                # Nodo normal - rectángulo beige
                lines.append(f'    {node_id}["{label}"]')
                lines.append(f"    style {node_id} fill:#FFE4B5,stroke:#DAA520")
            
            # Crear arista al padre
            if parent_id:
                lines.append(f"    {parent_id} --> {node_id}")
            
            # Procesar hijos
            for child in node.get("children", []):
                process_node(child, node_id)
        
        # Procesar desde la raíz
        if isinstance(tree, dict):
            process_node(tree)
        
        lines.append("```")
        return "\n".join(lines)
    
    def _generate_execution_flow_mermaid(
        self,
        flow: Dict[str, Any],
        algorithm_name: str
    ) -> str:
        """
        Genera diagrama Mermaid para flujo de ejecución.
        
        Args:
            flow: Datos del grafo de flujo
            algorithm_name: Nombre del algoritmo
            
        Returns:
            str: Código Mermaid
        """
        lines = [
            "```mermaid",
            "flowchart TD",
            f"    %% Flujo de Ejecución: {algorithm_name}",
            ""
        ]
        
        # Procesar nodos
        nodes = flow.get("nodes", [])
        edges = flow.get("edges", [])
        
        for node in nodes:
            node_id = self._sanitize_id(node.get("id", "unknown"))
            label = node.get("label", "?")
            node_type = node.get("type", "operation")
            
            # Forma del nodo según tipo
            if node_type == "decision":
                # Rombo para decisiones
                lines.append(f'    {node_id}{{{label}}}')
                lines.append(f"    style {node_id} fill:#FFD700,stroke:#B8860B")
            elif node_type == "loop":
                # Rectángulo redondeado para loops
                lines.append(f'    {node_id}([{label}])')
                lines.append(f"    style {node_id} fill:#FFA500,stroke:#FF8C00")
            elif node_type == "call":
                # Círculo para llamadas
                lines.append(f'    {node_id}(({label}))')
                lines.append(f"    style {node_id} fill:#87CEEB,stroke:#4682B4")
            else:
                # Rectángulo para operaciones
                lines.append(f'    {node_id}[{label}]')
                lines.append(f"    style {node_id} fill:#E0E0E0,stroke:#A9A9A9")
        
        lines.append("")
        
        # Procesar aristas
        for edge in edges:
            from_node = self._sanitize_id(edge.get("from", "?"))
            to_node = self._sanitize_id(edge.get("to", "?"))
            label = edge.get("label", "")
            
            if label:
                lines.append(f'    {from_node} -->|{label}| {to_node}')
            else:
                lines.append(f"    {from_node} --> {to_node}")
        
        lines.append("```")
        return "\n".join(lines)
    
    def _generate_complexity_diagram(self, data: ExportData) -> str:
        """
        Genera diagrama de complejidad.
        
        Args:
            data: Datos del análisis
            
        Returns:
            str: Código Mermaid
        """
        lines = [
            "```mermaid",
            "graph LR",
            f"    %% Análisis de Complejidad: {data.algorithm.name}",
            ""
        ]
        
        # Nodo central
        algo_id = self._sanitize_id(data.algorithm.name)
        lines.append(f'    {algo_id}["{data.algorithm.name}"]')
        lines.append(f"    style {algo_id} fill:#87CEEB,stroke:#4682B4,stroke-width:3px")
        lines.append("")
        
        # Complejidades temporales
        lines.append("    %% Complejidad Temporal")
        
        big_o = self.format_complexity(data.analysis.big_o)
        lines.append(f'    BigO["Big O<br/>{big_o}"]')
        lines.append(f"    style BigO fill:#FF6B6B,stroke:#DC143C")
        lines.append(f"    {algo_id} --> BigO")
        
        omega = self.format_complexity(data.analysis.omega)
        lines.append(f'    Omega["Omega<br/>{omega}"]')
        lines.append(f"    style Omega fill:#90EE90,stroke:#228B22")
        lines.append(f"    {algo_id} --> Omega")
        
        if data.analysis.theta:
            theta = self.format_complexity(data.analysis.theta)
            lines.append(f'    Theta["Theta<br/>{theta}"]')
            lines.append(f"    style Theta fill:#FFD93D,stroke:#FFA500")
            lines.append(f"    {algo_id} --> Theta")
        
        # Complejidad espacial
        if data.analysis.space_complexity:
            lines.append("")
            lines.append("    %% Complejidad Espacial")
            space = self.format_complexity(data.analysis.space_complexity)
            lines.append(f'    Space["Espacio<br/>{space}"]')
            lines.append(f"    style Space fill:#B19CD9,stroke:#8A2BE2")
            lines.append(f"    {algo_id} --> Space")
        
        lines.append("```")
        return "\n".join(lines)
    
    def _generate_patterns_diagram(self, data: ExportData) -> str:
        """
        Genera diagrama de patrones detectados.
        
        Args:
            data: Datos del análisis
            
        Returns:
            str: Código Mermaid
        """
        lines = [
            "```mermaid",
            "graph TD",
            f"    %% Patrones Detectados: {data.algorithm.name}",
            ""
        ]
        
        # Nodo central
        algo_id = self._sanitize_id(data.algorithm.name)
        lines.append(f'    {algo_id}["{data.algorithm.name}"]')
        lines.append(f"    style {algo_id} fill:#87CEEB,stroke:#4682B4,stroke-width:3px")
        lines.append("")
        
        # Patrón principal
        primary = data.patterns.primary_pattern
        primary_id = self._sanitize_id(f"pattern_{primary}")
        confidence = data.patterns.primary_confidence
        
        lines.append(f'    {primary_id}["{primary}<br/>Confianza: {confidence:.1%}"]')
        lines.append(f"    style {primary_id} fill:#90EE90,stroke:#228B22,stroke-width:2px")
        lines.append(f"    {algo_id} --> {primary_id}")
        lines.append("")
        
        # Otros patrones (top 3)
        lines.append("    %% Otros patrones detectados")
        for i, pattern in enumerate(data.patterns.patterns_found[:3]):
            if pattern.get("name") == primary:
                continue  # Skip primary
            
            name = pattern.get("name", "Desconocido")
            conf = pattern.get("confidence", 0)
            pattern_id = self._sanitize_id(f"pattern_{name}_{i}")
            
            lines.append(f'    {pattern_id}["{name}<br/>{conf:.1%}"]')
            lines.append(f"    style {pattern_id} fill:#FFE4B5,stroke:#DAA520")
            lines.append(f"    {algo_id} --> {pattern_id}")
        
        lines.append("```")
        return "\n".join(lines)

def export_to_mermaid(
    data: ExportData,
    output_path: str = None
) -> ExportResult:
    """
    Helper para exportar a Mermaid rápidamente.
    
    Args:
        data: Datos a exportar
        output_path: Ruta de salida (opcional)
        
    Returns:
        ExportResult: Resultado de la exportación
    """
    from pathlib import Path
    from app.infrastructure.export.base_exporter import ExportConfig
    
    config = ExportConfig(
        format=ExportFormat.MERMAID,
        output_path=Path(output_path) if output_path else None
    )
    
    exporter = MermaidExporter(config)
    return exporter.export(data)