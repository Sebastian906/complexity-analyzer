"""
Script de Demostración - Sistema de Exportación

Demuestra el uso completo del sistema de exportación:
1. Parseo de algoritmo
2. Análisis de complejidad
3. Detección de patrones
4. Exportación a múltiples formatos

Uso:
    python scripts/demo_export.py
"""

import time
import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax

from app.core.parser.pseudocode_parser import PseudocodeParser
from app.core.analyzer.complexity import ComplexityCalculator
from app.core.patterns.pattern_detector import PatternDetector
from app.infrastructure.database.models.mongo import (
    Algorithm,
    AnalysisResult,
    PatternDetection
)
from app.infrastructure.export import (
    ExportFormat,
    export_analysis,
    export_to_multiple_formats,
    ExporterFactory,
    PDF_AVAILABLE,
    EXCEL_AVAILABLE,
)
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

console = Console()

# ALGORITMOS DE EJEMPLO
EXAMPLE_ALGORITHMS = {
    "quicksort": {
        "code": """algorithm quicksort(A[1..n])
begin
    if n > 1 then
    begin
        q ← partition(A, 1, n)
        call quicksort(A[1..q-1])
        call quicksort(A[q+1..n])
    end
end""",
        "description": "Algoritmo de ordenamiento QuickSort (Divide y Conquista)"
    },
    
    "binary_search": {
        "code": """algorithm binary_search(A[1..n], x)
begin
    low ← 1
    high ← n
    while low <= high do
    begin
        mid ← (low + high) / 2
        if A[mid] = x then
            return mid
        else if A[mid] < x then
            low ← mid + 1
        else
            high ← mid - 1
    end
    return -1
end""",
        "description": "Búsqueda binaria en arreglo ordenado"
    },
    
    "bubble_sort": {
        "code": """algorithm bubble_sort(A[1..n])
begin
    for i ← 1 to n-1 do
    begin
        for j ← 1 to n-i do
        begin
            if A[j] > A[j+1] then
            begin
                temp ← A[j]
                A[j] ← A[j+1]
                A[j+1] ← temp
            end
        end
    end
end""",
        "description": "Ordenamiento por burbuja (fuerza bruta)"
    },
    
    "fibonacci": {
        "code": """algorithm fibonacci(n)
begin
    if n <= 1 then
        return n
    else
        return fibonacci(n-1) + fibonacci(n-2)
end""",
        "description": "Fibonacci recursivo (exponencial)"
    },
    
    "merge_sort": {
        "code": """algorithm merge_sort(A[1..n])
begin
    if n > 1 then
    begin
        mid ← n / 2
        call merge_sort(A[1..mid])
        call merge_sort(A[mid+1..n])
        call merge(A, 1, mid, n)
    end
end""",
        "description": "MergeSort (Divide y Conquista)"
    }
}

# FUNCIONES AUXILIARES
def print_banner():
    """Imprime banner del demo"""
    console.print(Panel.fit(
        "[bold cyan]Sistema de Exportación de Análisis de Complejidad[/bold cyan]\n"
        "[yellow]Demo Completo - Análisis y Exportación de Algoritmos[/yellow]\n"
        f"[dim]Entorno: {settings.APP_ENV} | Debug: {settings.DEBUG}[/dim]",
        border_style="cyan"
    ))

def print_formats_table():
    """Muestra tabla de formatos disponibles"""
    table = Table(title="Formatos de Exportación Disponibles", show_header=True)
    table.add_column("Formato", style="cyan", width=12)
    table.add_column("Estado", justify="center", style="green", width=8)
    table.add_column("Descripción", style="white")
    table.add_column("Extensión", style="yellow", width=10)
    
    formats_info = [
        (ExportFormat.JSON, True, "Datos estructurados", ".json"),
        (ExportFormat.MARKDOWN, True, "Documentación en Markdown", ".md"),
        (ExportFormat.CSV, True, "Datos tabulares", ".csv"),
        (ExportFormat.HTML, True, "Visualización web", ".html"),
        (ExportFormat.DOT, True, "Graphviz diagrams", ".dot"),
        (ExportFormat.MERMAID, True, "Mermaid diagrams", ".mmd"),
        (ExportFormat.SVG, True, "Gráficos vectoriales", ".svg"),
        (ExportFormat.PDF, PDF_AVAILABLE, "Reportes profesionales", ".pdf"),
        (ExportFormat.EXCEL, EXCEL_AVAILABLE, "Hojas de cálculo", ".xlsx"),
    ]
    
    for format_type, available, desc, ext in formats_info:
        status = "✓" if available else "✗"
        style = "green" if available else "red"
        table.add_row(
            format_type.value.upper(),
            f"[{style}]{status}[/{style}]",
            desc,
            ext
        )
    
    console.print(table)
    console.print()

def show_algorithm_menu():
    """Muestra menú de selección de algoritmos"""
    console.print("[bold]Algoritmos Disponibles para Demo:[/bold]\n")
    
    table = Table(show_header=True)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Nombre", style="magenta", width=20)
    table.add_column("Descripción", style="white")
    
    for i, (name, info) in enumerate(EXAMPLE_ALGORITHMS.items(), 1):
        table.add_row(str(i), name, info["description"])
    
    console.print(table)
    console.print()

async def analyze_algorithm(name: str, code: str, description: str = "") -> tuple:
    """
    Analiza un algoritmo completo.
    
    Returns:
        tuple: (Algorithm, AnalysisResult, PatternDetection)
    """
    console.print(f"\n[bold yellow]Analizando: {name}[/bold yellow]")
    if description:
        console.print(f"[dim]{description}[/dim]\n")
    
    # Mostrar código
    console.print("[cyan]Código del algoritmo:[/cyan]")
    syntax = Syntax(code, "text", theme="monokai", line_numbers=True)
    console.print(syntax)
    console.print()
    
    # 1. Crear modelo de algoritmo
    algorithm = Algorithm(
        name=name,
        code=code,
        language="pseudocode",
        category="demo",
        tags=["demo"],
        description=description,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Guardar en BD para obtener ID
    try:
        await algorithm.insert()
        console.print(f"[green]✓[/green] Algoritmo guardado en BD (ID: {algorithm.id})")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] No se pudo guardar en BD: {e}")
    
    # 2. Parsear
    with console.status("[cyan]Parseando algoritmo..."):
        try:
            parser = PseudocodeParser()
            ast = parser.parse(code)
            console.print("[green]✓[/green] Parseado exitosamente")
        except Exception as e:
            console.print(f"[red]✗[/red] Error en parseo: {str(e)}")
            raise
    
    # 3. Analizar complejidad
    start_time = time.time()
    
    with console.status("[cyan]Analizando complejidad..."):
        try:
            calculator = ComplexityCalculator()
            complexity_result = calculator.analyze_all(ast)
            
            analysis_time = time.time() - start_time
            
            # Crear modelo de resultado
            analysis = AnalysisResult(
                algorithm=algorithm,
                big_o=complexity_result.get("big_o", "O(?)"),
                omega=complexity_result.get("omega", "Ω(?)"),
                theta=complexity_result.get("theta", "Θ(?)"),
                space_complexity=complexity_result.get("space", "O(1)"),
                temporal_recurrence=complexity_result.get("recurrence", None),
                spatial_recurrence=complexity_result.get("spatial_recurrence", None),
                line_by_line=complexity_result.get("line_by_line", {}),
                analysis_time=analysis_time,
                analyzer_version="1.0.0",
                created_at=datetime.now(timezone.utc)
            )
            
            # Guardar en BD
            try:
                await analysis.insert()
                console.print("[green]✓[/green] Análisis guardado en BD")
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] No se pudo guardar análisis: {e}")
            
            console.print("[green]✓[/green] Análisis de complejidad completado")
        except Exception as e:
            console.print(f"[red]✗[/red] Error en análisis: {str(e)}")
            raise
    
    # 4. Detectar patrones
    detection_start_time = time.time()

    with console.status("[cyan]Detectando patrones algorítmicos..."):
        try:
            detector = PatternDetector()
            patterns_result = detector.detect(ast, min_confidence=0.3)

            # Obtener patrón primario
            primary_pattern = patterns_result.primary_pattern
            primary_pattern_name = primary_pattern.pattern.pattern_name if primary_pattern else "Desconocido"
            primary_confidence = primary_pattern.final_score if primary_pattern else 0.0

            # Extraer datos de ScoredPattern correctamente
            all_patterns_data = []
            for scored_pattern in patterns_result.all_patterns:
                try:
                    # ScoredPattern.pattern es un PatternMatch que tiene:
                    # - pattern_name: str
                    # - confidence: float (score base)
                    # - pattern_type: PatternType
                    # - indicators_found: List[PatternIndicator]  ← Correcto nombre
                    # - indicators_missing: List[PatternIndicator]

                    pattern_name = scored_pattern.pattern.pattern_name
                    final_score = scored_pattern.final_score  # Score ajustado
                    pattern_type = scored_pattern.pattern.pattern_type.value
                    base_confidence = scored_pattern.pattern.confidence  # Score base

                    # El atributo correcto es indicators_found (no indicators)
                    indicators_found = scored_pattern.pattern.indicators_found
                    evidence_count = len(indicators_found)

                    pattern_dict = {
                        "pattern": pattern_name,
                        "confidence": final_score,  # Score ajustado
                        "type": pattern_type,
                        "name": pattern_name,
                        "score": base_confidence,  # Score base sin ajustar
                        "evidence": evidence_count
                    }
                    all_patterns_data.append(pattern_dict)

                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] Error procesando patrón: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            # Obtener estructuras del metadata
            structures_found = patterns_result.metadata.get("structures", [])

            # Calcular tiempo de detección
            detection_time = time.time() - detection_start_time

            # Crear el modelo PatternDetection
            patterns = PatternDetection(
                algorithm=algorithm,
                primary_pattern=primary_pattern_name,
                primary_confidence=primary_confidence,
                patterns_found=all_patterns_data,
                structures_found=structures_found,
                detection_time=detection_time,
                created_at=datetime.now(timezone.utc)
            )

            # Guardar en BD
            try:
                await patterns.insert()
                console.print("[green]✓[/green] Patrones guardados en BD")
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] No se pudo guardar patrones: {e}")

            # Mostrar resumen
            console.print(f"[green]✓[/green] Patrones detectados: {primary_pattern_name} ({primary_confidence:.1%})")
            if len(all_patterns_data) > 1:
                console.print(f"[dim]  Patrones adicionales: {len(all_patterns_data) - 1}[/dim]")

        except Exception as e:
            console.print(f"[red]✗[/red] Error en detección de patrones: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    return algorithm, analysis, patterns

def show_analysis_results(algorithm, analysis, patterns):
    """Muestra resultados del análisis en formato tabular"""
    console.print("\n[bold cyan]Resultados del Análisis:[/bold cyan]\n")
    
    # Tabla de complejidades
    complexity_table = Table(title="Complejidades", show_header=True)
    complexity_table.add_column("Métrica", style="cyan", width=20)
    complexity_table.add_column("Valor", style="magenta")
    
    complexity_table.add_row("Big O (Peor caso)", analysis.big_o)
    complexity_table.add_row("Omega (Mejor caso)", analysis.omega)
    complexity_table.add_row("Theta (Caso promedio)", analysis.theta)
    complexity_table.add_row("Complejidad Espacial", analysis.space_complexity)
    
    # Verificar si hay recurrencia temporal
    if hasattr(analysis, 'temporal_recurrence') and analysis.temporal_recurrence:
        complexity_table.add_row("Recurrencia Temporal", analysis.temporal_recurrence)
    
    console.print(complexity_table)
    console.print()
    
    # Tabla de patrones
    if patterns.patterns_found:
        pattern_table = Table(title="Patrones Detectados", show_header=True)
        pattern_table.add_column("Patrón", style="cyan")
        pattern_table.add_column("Confianza", style="green", justify="right")
        
        # Mostrar hasta 5 patrones con manejo de errores
        for pattern in patterns.patterns_found[:5]:
            # Usar .get() para evitar KeyError
            pattern_name = pattern.get("pattern") or pattern.get("name", "Desconocido")
            confidence = pattern.get("confidence", 0.0)
            pattern_table.add_row(pattern_name, f"{confidence*100:.1f}%")
        
        console.print(pattern_table)
        console.print()
    
    # Información del patrón primario
    console.print(f"[bold]Patrón Principal:[/bold] [yellow]{patterns.primary_pattern}[/yellow]")
    console.print(f"[bold]Confianza:[/bold] [green]{patterns.primary_confidence*100:.1f}%[/green]\n")

def export_to_format(algorithm, analysis, patterns, format_type: ExportFormat, output_dir: Path) -> tuple:
    """Exporta a un formato específico"""
    try:
        output_path = output_dir / f"{algorithm.name}.{format_type.value}"
        
        result = export_analysis(
            algorithm=algorithm,
            analysis=analysis,
            patterns=patterns,
            format=format_type,
            output_path=str(output_path)
        )
        
        if result.success:
            file_size = output_path.stat().st_size if output_path.exists() else 0
            return True, output_path, file_size
        else:
            return False, None, 0
            
    except Exception as e:
        console.print(f"[red]Error exportando a {format_type.value}: {e}[/red]")
        return False, None, 0

# MAIN DEMO
async def main():
    """Función principal del demo"""
    # Inicializar Beanie y MongoDB
    try:
        mongodb_url = getattr(settings, "MONGODB_URL", "mongodb://localhost:27017")
        mongodb_db_name = getattr(settings, "MONGODB_DB_NAME", "complexity_analyzer")
        
        client = AsyncIOMotorClient(mongodb_url)
        await init_beanie(
            database=client[mongodb_db_name],
            document_models=[Algorithm, AnalysisResult, PatternDetection]
        )
        console.print("[dim]MongoDB inicializado[/dim]")
    except Exception as e:
        console.print(f"[yellow]MongoDB no disponible: {e}[/yellow]")
        console.print("[dim]Continuando sin persistencia...[/dim]")
    
    print_banner()
    print_formats_table()
    
    # Crear directorio de salida
    output_dir = settings.EXPORTS_PATH
    output_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[cyan]Directorio de salida:[/cyan] [white]{output_dir.absolute()}[/white]\n")
    
    # Mostrar menú de algoritmos
    show_algorithm_menu()
    
    # Para el demo, usar QuickSort por defecto
    selected = "quicksort"
    console.print(f"[bold green]✓ Algoritmo seleccionado:[/bold green] [yellow]{selected}[/yellow]\n")
    
    algo_info = EXAMPLE_ALGORITHMS[selected]
    
    # Analizar
    try:
        algorithm, analysis, patterns = await analyze_algorithm(
            selected,
            algo_info["code"],
            algo_info["description"]
        )
    except Exception as e:
        console.print(f"\n[bold red]Error en análisis: {str(e)}[/bold red]")
        return
    
    # Mostrar resultados
    show_analysis_results(algorithm, analysis, patterns)
    
    # Exportar a todos los formatos disponibles
    console.print("[bold cyan]Exportando a múltiples formatos:[/bold cyan]\n")
    
    formats_to_export = ExporterFactory.get_available_formats()
    successful = 0
    failed = 0
    results = {}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task(
            "[cyan]Exportando...",
            total=len(formats_to_export)
        )
        
        for format_type in formats_to_export:
            progress.update(task, description=f"[cyan]Exportando a {format_type.value.upper()}...")
            
            success, path, size = export_to_format(
                algorithm, analysis, patterns, format_type, output_dir
            )
            
            if success:
                successful += 1
                results[format_type] = (True, path, size)
            else:
                failed += 1
                results[format_type] = (False, None, 0)
            
            progress.update(task, advance=1)
    
    # Tabla de resultados
    console.print("\n[bold cyan]Resultados de Exportación:[/bold cyan]\n")
    
    results_table = Table(title="Exportación por Formato", show_header=True)
    results_table.add_column("Formato", style="cyan", width=12)
    results_table.add_column("Estado", justify="center", width=8)
    results_table.add_column("Archivo", style="white")
    results_table.add_column("Tamaño", style="yellow", justify="right", width=15)
    
    for format_type, (success, path, size) in results.items():
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        filename = path.name if path else "N/A"
        size_str = f"{size:,} B ({size/1024:.2f} KB)" if size > 0 else "N/A"
        
        results_table.add_row(
            format_type.value.upper(),
            status,
            filename,
            size_str
        )
    
    console.print(results_table)
    
    # Resumen final
    console.print(f"\n[bold green]Exportación completada:[/bold green]")
    console.print(f"  [green]Exitosos:[/green] {successful}")
    console.print(f"  [red]Fallidos:[/red] {failed}")
    console.print(f"  [cyan]Total:[/cyan] {len(formats_to_export)}")
    
    # Demo adicional: Exportación múltiple simultánea
    console.print(f"\n[bold cyan]Demo: Exportación múltiple simultánea[/bold cyan]")
    console.print("[dim]Usando la función helper export_to_multiple_formats()[/dim]\n")
    
    multi_formats = [ExportFormat.JSON, ExportFormat.MARKDOWN, ExportFormat.HTML]
    
    with console.status("[cyan]Exportando..."):
        multi_results = export_to_multiple_formats(
            algorithm=algorithm,
            analysis=analysis,
            patterns=patterns,
            formats=multi_formats,
            output_dir=str(output_dir)
        )
    
    for format_type, result in multi_results.items():
        status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
        console.print(f"  {status} {format_type.value.upper()}")
    
    # Banner final
    console.print(Panel.fit(
        "[bold green]🎉 ¡Demo completado exitosamente![/bold green]\n\n"
        f"[cyan]Archivos generados en:[/cyan]\n"
        f"[white]{output_dir.absolute()}[/white]\n\n"
        f"[dim]Puedes abrir los archivos con tu editor favorito[/dim]",
        border_style="green"
    ))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrumpido por el usuario[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()