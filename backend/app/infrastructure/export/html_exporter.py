"""
HTML Exporter - Exportador a formato HTML

Exporta resultados de análisis a HTML interactivo
con CSS moderno y JavaScript para visualización dinámica.
"""

import time
import json
import html as html_module
from typing import Dict, Any

from app.infrastructure.export.base_exporter import (
    BaseExporter,
    ExportData,
    ExportFormat,
    ExportResult
)

class HTMLExporter(BaseExporter):
    """
    Exportador a formato HTML.
    
    Genera páginas HTML autocontenidas con:
    - CSS integrado (sin dependencias externas)
    - JavaScript para interactividad
    - Diseño responsivo
    - Gráficos y visualizaciones
    """
    
    def get_format(self) -> ExportFormat:
        """Retorna el formato HTML"""
        return ExportFormat.HTML
    
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos a formato HTML.
        
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
            
            # Generar HTML completo
            html_content = self._generate_html(data)
            
            # Guardar archivo
            output_path = self.prepare_output_path(data)
            file_size = self.save_to_file(html_content, output_path)
            
            export_time = time.time() - start_time
            
            self.logger.info(f"Exportación HTML completada en {export_time:.3f}s")
            
            return self.create_result(
                success=True,
                output_path=output_path,
                file_size=file_size,
                export_time=export_time,
                html_size=len(html_content)
            )
            
        except Exception as e:
            self.logger.error(f"Error en exportación HTML: {str(e)}")
            return self.create_result(
                success=False,
                errors=[str(e)],
                export_time=time.time() - start_time
            )
    
    def _generate_html(self, data: ExportData) -> str:
        """
        Genera documento HTML completo.
        
        Args:
            data: Datos a exportar
            
        Returns:
            str: Contenido HTML
        """
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis: {html_module.escape(data.algorithm.name)}</title>
    <style>
        {self._generate_css()}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_header(data)}
        {self._generate_summary_section(data)}
        {self._generate_code_section(data)}
        {self._generate_complexity_section(data)}
        {self._generate_patterns_section(data)}
        {self._generate_visualizations_section(data)}
        {self._generate_footer(data)}
    </div>
    <script>
        {self._generate_javascript(data)}
    </script>
</body>
</html>"""
    
    def _generate_css(self) -> str:
        """Genera estilos CSS"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .section {
            padding: 40px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .section:last-of-type {
            border-bottom: none;
        }
        
        .section-title {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #667eea;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }
        
        .card {
            background: #f9f9f9;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
        
        .card-title {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #444;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .info-item {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .info-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        
        .info-value {
            font-size: 1.4em;
            font-weight: bold;
            color: #333;
        }
        
        .complexity-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .badge-big-o {
            background: #ff6b6b;
            color: white;
        }
        
        .badge-omega {
            background: #90ee90;
            color: #333;
        }
        
        .badge-theta {
            background: #ffd93d;
            color: #333;
        }
        
        .badge-space {
            background: #b19cd9;
            color: white;
        }
        
        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            line-height: 1.5;
        }
        
        .pattern-list {
            list-style: none;
        }
        
        .pattern-item {
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #87ceeb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .pattern-name {
            font-weight: bold;
            color: #333;
        }
        
        .confidence-bar {
            width: 200px;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s ease;
        }
        
        footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-top: 5px;
        }
        
        .tab-container {
            margin-top: 20px;
        }
        
        .tabs {
            display: flex;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 20px;
        }
        
        .tab {
            padding: 12px 24px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1em;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
            font-weight: bold;
        }
        
        .tab:hover {
            color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @media (max-width: 768px) {
            .info-grid {
                grid-template-columns: 1fr;
            }
            
            header h1 {
                font-size: 1.8em;
            }
            
            .section {
                padding: 20px;
            }
        }
        """
    
    def _generate_header(self, data: ExportData) -> str:
        """Genera el encabezado"""
        return f"""
        <header>
            <h1>{html_module.escape(data.algorithm.name)}</h1>
            <p class="subtitle">Análisis de Complejidad Algorítmica</p>
            <p style="margin-top: 10px; opacity: 0.8;">
                Generado: {self.format_timestamp(data.timestamp)}
            </p>
        </header>
        """
    
    def _generate_summary_section(self, data: ExportData) -> str:
        """Genera sección de resumen"""
        html = '<div class="section">'
        html += '<h2 class="section-title">Resumen</h2>'
        html += '<div class="info-grid">'
        
        # Información básica
        info_items = [
            ("Lenguaje", html_module.escape(data.algorithm.language)),
            ("Categoría", html_module.escape(data.algorithm.category or "No especificada")),
            ("Tiempo de análisis", f"{data.analysis.analysis_time:.3f}s"),
        ]
        
        if data.patterns:
            info_items.append(("Patrón principal", data.patterns.primary_pattern))
        
        for label, value in info_items:
            html += f"""
            <div class="info-item">
                <div class="info-label">{html_module.escape(str(label))}</div>
                <div class="info-value">{html_module.escape(str(value))}</div>
            </div>
            """
        
        html += '</div></div>'
        return html
    
    def _generate_code_section(self, data: ExportData) -> str:
        """Genera sección de código"""
        if not self.config.include_code:
            return ""
        
        code_escaped = (data.algorithm.code
                       .replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;'))
        
        return f"""
        <div class="section">
            <h2 class="section-title">Código Fuente</h2>
            <pre><code>{code_escaped}</code></pre>
        </div>
        """
    
    def _generate_complexity_section(self, data: ExportData) -> str:
        """Genera sección de complejidad"""
        html = '<div class="section">'
        html += '<h2 class="section-title">Análisis de Complejidad</h2>'
        html += '<div class="stats-grid">'
        
        # Big O
        html += f"""
        <div class="stat-box">
            <div class="stat-value">{self.format_complexity(data.analysis.big_o)}</div>
            <div class="stat-label">Big O (Peor caso)</div>
        </div>
        """
        
        # Omega
        html += f"""
        <div class="stat-box">
            <div class="stat-value">{self.format_complexity(data.analysis.omega)}</div>
            <div class="stat-label">Omega (Mejor caso)</div>
        </div>
        """
        
        # Theta
        if data.analysis.theta:
            html += f"""
            <div class="stat-box">
                <div class="stat-value">{self.format_complexity(data.analysis.theta)}</div>
                <div class="stat-label">Theta (Promedio)</div>
            </div>
            """
        
        # Espacio
        if data.analysis.space_complexity:
            html += f"""
            <div class="stat-box">
                <div class="stat-value">{self.format_complexity(data.analysis.space_complexity)}</div>
                <div class="stat-label">Complejidad Espacial</div>
            </div>
            """
        
        html += '</div>'
        
        # Recurrencias
        if data.analysis.temporal_recurrence or data.analysis.spatial_recurrence:
            html += '<div class="card" style="margin-top: 20px;">'
            html += '<h3 class="card-title">Ecuaciones de Recurrencia</h3>'
            
            if data.analysis.temporal_recurrence:
                html += f'<p><strong>Temporal:</strong> {data.analysis.temporal_recurrence}</p>'
            
            if data.analysis.spatial_recurrence:
                html += f'<p><strong>Espacial:</strong> {data.analysis.spatial_recurrence}</p>'
            
            html += '</div>'
        
        html += '</div>'
        return html
    
    def _generate_patterns_section(self, data: ExportData) -> str:
        """Genera sección de patrones"""
        if not data.patterns or not data.patterns.patterns_found:
            return ""
        
        html = '<div class="section">'
        html += '<h2 class="section-title">Patrones Detectados</h2>'
        html += '<ul class="pattern-list">'
        
        for pattern in data.patterns.patterns_found[:5]:
            name = pattern.get("name", "Desconocido")
            confidence = pattern.get("confidence", 0)
            
            html += f"""
            <li class="pattern-item">
                <span class="pattern-name">{html_module.escape(str(name))}</span>
                <div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: {confidence * 100}%"></div>
                    </div>
                    <small>{confidence:.1%}</small>
                </div>
            </li>
            """
        
        html += '</ul></div>'
        return html
    
    def _generate_visualizations_section(self, data: ExportData) -> str:
        """Genera sección de visualizaciones"""
        if not data.visualizations:
            return ""
        
        return """
        <div class="section">
            <h2 class="section-title">Visualizaciones</h2>
            <div class="card">
                <p>Las visualizaciones se encuentran en archivos separados (SVG, DOT, etc.)</p>
            </div>
        </div>
        """
    
    def _generate_footer(self, data: ExportData) -> str:
        """Genera el pie de página"""
        return f"""
        <footer>
            <p>Generado por Complexity Analyzer v{data.analysis.analyzer_version}</p>
            <p>{self.format_timestamp(data.timestamp)}</p>
        </footer>
        """
    
    def _generate_javascript(self, data: ExportData) -> str:
        """Genera código JavaScript para interactividad"""
        return """
        // Tab switching
        function switchTab(tabName) {
            const tabs = document.querySelectorAll('.tab');
            const contents = document.querySelectorAll('.tab-content');
            
            tabs.forEach(tab => tab.classList.remove('active'));
            contents.forEach(content => content.classList.remove('active'));
            
            document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }
        
        // Animate confidence bars on load
        window.addEventListener('load', () => {
            const bars = document.querySelectorAll('.confidence-fill');
            bars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            });
        });
        """

def export_to_html(
    data: ExportData,
    output_path: str = None
) -> ExportResult:
    """
    Helper para exportar a HTML rápidamente.
    
    Args:
        data: Datos a exportar
        output_path: Ruta de salida (opcional)
        
    Returns:
        ExportResult: Resultado de la exportación
    """
    from pathlib import Path
    from app.infrastructure.export.base_exporter import ExportConfig
    
    config = ExportConfig(
        format=ExportFormat.HTML,
        output_path=Path(output_path) if output_path else None
    )
    
    exporter = HTMLExporter(config)
    return exporter.export(data)