"""
Demo Script - Módulo de Servicios

Demuestra todas las funcionalidades del módulo de servicios.

Uso:
    python scripts/demo_services.py
"""

import asyncio
import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.services import (
    AlgorithmService,
    AlgorithmCreateRequest,
    AlgorithmSearchCriteria,
    AlgorithmCategory,
    AnalysisOrchestrator,
    CompleteAnalysisRequest,
    ValidationService,
    ValidationRequest,
    ValidationLevel,
    ExportService,
    ExportRequest,
    ExportFormat,
    CacheService,
    CacheKey,
    generate_cache_key,
)

console = Console()

# Algoritmos de Ejemplo
SAMPLE_ALGORITHMS = {
    "bubble_sort": """
algorithm bubbleSort(A[n])
begin
    for i ← 1 to n - 1 do
    begin
        for j ← 1 to n - i do
        begin
            if (A[j] > A[j + 1]) then
            begin
                temp ← A[j]
                A[j] ← A[j + 1]
                A[j + 1] ← temp
            end
        end
    end
end
    """.strip(),

    "binary_search": """
algorithm binarySearch(A[n], x)
begin
    left ← 1
    right ← n

    while (left <= right) do
    begin
        mid ← (left + right) / 2

        if (A[mid] = x) then
        begin
            return mid
        end

        if (A[mid] < x) then
        begin
            left ← mid + 1
        end
        else
        begin
            right ← mid - 1
        end
    end

    return -1
end
    """.strip(),

    "fibonacci": """
algorithm fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end

    return fibonacci(n - 1) + fibonacci(n - 2)
end
    """.strip(),
}

# Demos
async def demo_algorithm_service():
    """Demo: AlgorithmService"""
    console.print(Panel.fit(
        "[bold cyan]Demo: AlgorithmService[/bold cyan]",
        border_style="cyan"
    ))

    # Crear servicio
    service = AlgorithmService()

    # 1. Crear algoritmos
    console.print("\n[bold]1. Creando algoritmos...[/bold]")

    algorithms = []
    for name, code in SAMPLE_ALGORITHMS.items():
        request = AlgorithmCreateRequest(
            code=code,
            category=AlgorithmCategory.SORTING if "sort" in name.lower() else AlgorithmCategory.SEARCHING,
            tags=[name.replace("_", " ")],
        )

        algo = await service.create(request)
        algorithms.append(algo)
        console.print(f"  ✓ Creado: [green]{algo.metadata.name}[/green] (ID: {algo.metadata.id[:8]}...)")

    # 2. Buscar
    console.print("\n[bold]2. Buscando algoritmos de ordenamiento...[/bold]")

    criteria = AlgorithmSearchCriteria(category=AlgorithmCategory.SORTING)
    results = await service.search(criteria)

    console.print(f"  Encontrados: [cyan]{len(results)}[/cyan] algoritmos")
    for algo in results:
        console.print(f"    • {algo.name} ({algo.category.value})")

    # 3. Estadísticas
    console.print("\n[bold]3. Estadísticas del servicio:[/bold]")
    stats = service.get_statistics()

    table = Table(show_header=True)
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="magenta")

    table.add_row("Total algoritmos", str(stats["total_algorithms"]))
    table.add_row("Por categoría", str(stats["by_category"]))
    table.add_row("Storage path", str(stats["storage_path"]))

    console.print(table)

    return algorithms[0]  # Retornar primer algoritmo para siguientes demos

async def demo_validation_service():
    """Demo: ValidationService"""
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold cyan]Demo: ValidationService[/bold cyan]",
        border_style="cyan"
    ))

    service = ValidationService()

    # Código válido
    valid_code = SAMPLE_ALGORITHMS["bubble_sort"]

    # Código inválido
    invalid_code = """
algorithm invalid(n
begin
    x ← 1
end
    """

    # 1. Validación sintaxis - válido
    console.print("\n[bold]1. Validación sintaxis (código válido):[/bold]")

    result = await service.validate(
        ValidationRequest(code=valid_code, level=ValidationLevel.SYNTAX)
    )

    if result.is_valid:
        console.print("  [green]✓ Código sintácticamente válido[/green]")
    else:
        console.print("  [red]✗ Errores encontrados[/red]")
        for error in result.errors:
            console.print(f"    • {error.message}")

    # 2. Validación sintaxis - inválido
    console.print("\n[bold]2. Validación sintaxis (código inválido):[/bold]")

    result = await service.validate(
        ValidationRequest(code=invalid_code, level=ValidationLevel.SYNTAX)
    )

    if result.is_valid:
        console.print("  [green]✓ Válido[/green]")
    else:
        console.print(f"  [red]✗ {len(result.errors)} error(es) encontrado(s)[/red]")
        for error in result.errors[:3]:  # Solo mostrar primeros 3
            console.print(f"    • {error.message}")

    # 3. Validación completa
    console.print("\n[bold]3. Validación completa con best practices:[/bold]")

    result = await service.validate(
        ValidationRequest(
            code=valid_code,
            level=ValidationLevel.COMPLETE,
            check_best_practices=True
        )
    )

    console.print(f"  Errores: [red]{len(result.errors)}[/red]")
    console.print(f"  Warnings: [yellow]{len(result.warnings)}[/yellow]")
    console.print(f"  Infos: [blue]{len(result.infos)}[/blue]")

async def demo_analysis_orchestrator():
    """Demo: AnalysisOrchestrator"""
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold cyan]Demo: AnalysisOrchestrator[/bold cyan]",
        border_style="cyan"
    ))

    orchestrator = AnalysisOrchestrator()
    code = SAMPLE_ALGORITHMS["bubble_sort"]

    console.print("\n[bold]Ejecutando análisis completo...[/bold]")
    console.print(f"Código: [dim]{code[:50]}...[/dim]")

    # Análisis con progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Analizando...", total=None)

        request = CompleteAnalysisRequest(
            code=code,
            analyze_complexity=True,
            analyze_patterns=True,
            analyze_structures=True,
            generate_visualizations=False,  # Skip para demo rápido
        )

        result = await orchestrator.analyze_complete(request)

        progress.update(task, completed=True)

    # Mostrar resultados
    console.print(f"\n[bold]Estado:[/bold] [{'green' if result.success else 'red'}]{result.status.value}[/]")
    console.print(f"[bold]Duración:[/bold] {result.total_duration:.2f}s")
    console.print(f"[bold]Pasos completados:[/bold] {len(result.successful_steps)}/{len(result.steps)}")

    # Tabla de pasos
    table = Table(title="Pasos del Análisis")
    table.add_column("Paso", style="cyan")
    table.add_column("Estado", style="magenta")
    table.add_column("Duración (s)", style="yellow")

    for step in result.steps:
        status = "✓" if step.success else "✗"
        table.add_row(
            step.step.value,
            f"[{'green' if step.success else 'red'}]{status}[/]",
            f"{step.duration:.3f}"
        )

    console.print(table)

    # Complejidad
    if result.complexity_result:
        console.print("\n[bold]Complejidad:[/bold]")
        console.print(f"  • Big O:  [cyan]{result.complexity_result['big_o']}[/cyan]")
        console.print(f"  • Omega:  [cyan]{result.complexity_result['omega']}[/cyan]")
        console.print(f"  • Theta:  [cyan]{result.complexity_result.get('theta', 'N/A')}[/cyan]")

    # Patrón
    if result.patterns_result and result.patterns_result.get('primary_pattern'):
        primary = result.patterns_result['primary_pattern']
        console.print(f"\n[bold]Patrón detectado:[/bold] {primary['name']}")
        console.print(f"  Confianza: {primary['confidence']:.2%}")

    # Estructura
    if result.structures_result and result.structures_result.get('primary_structure'):
        primary = result.structures_result['primary_structure']
        console.print(f"\n[bold]Estructura detectada:[/bold] {primary['name']}")
        console.print(f"  Confianza: {primary['confidence']:.2%}")

    # Resumen
    if result.summary:
        console.print("\n[bold]Resumen:[/bold]")
        console.print(Panel(result.summary, border_style="dim"))

    return result

async def demo_export_service(analysis_result):
    """Demo: ExportService"""
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold cyan]Demo: ExportService[/bold cyan]",
        border_style="cyan"
    ))

    service = ExportService()

    # Preparar datos para exportar
    data = {
        "algorithm_name": analysis_result.algorithm_name,
        "complexity_result": analysis_result.complexity_result,
        "patterns_result": analysis_result.patterns_result,
        "summary": analysis_result.summary,
    }

    # Exportar en diferentes formatos
    formats = [
        (ExportFormat.JSON, "json"),
        (ExportFormat.MARKDOWN, "md"),
        (ExportFormat.TXT, "txt"),
        (ExportFormat.HTML, "html"),
    ]

    console.print("\n[bold]Exportando en múltiples formatos:[/bold]")

    for format_enum, ext in formats:
        request = ExportRequest(
            data=data,
            format=format_enum,
            filename=f"demo_export.{ext}"
        )

        result = await service.export(request)

        if result.success:
            status = "[green]✓[/green]"
            size_kb = result.size_bytes / 1024
            console.print(f"  {status} {format_enum.value.upper()}: {size_kb:.2f} KB")
            if result.file_path:
                console.print(f"      → {result.file_path}")

            # Mostrar preview del JSON
            if format_enum == ExportFormat.JSON and result.content:
                syntax = Syntax(result.content[:300] + "...", "json", theme="monokai")
                console.print("\n[dim]Preview JSON:[/dim]")
                console.print(syntax)
        else:
            console.print(f"  [red]✗[/red] {format_enum.value.upper()}: {result.error}")

async def demo_cache_service():
    """Demo: CacheService"""
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold cyan]Demo: CacheService[/bold cyan]",
        border_style="cyan"
    ))

    cache = CacheService()
    code = SAMPLE_ALGORITHMS["fibonacci"]

    # 1. Generar clave
    console.print("\n[bold]1. Generando clave de caché:[/bold]")
    cache_key = generate_cache_key(CacheKey.ANALYSIS, code)
    console.print(f"  Clave: [cyan]{cache_key}[/cyan]")

    # 2. Guardar en caché
    console.print("\n[bold]2. Guardando en caché:[/bold]")
    data = {"big_o": "O(2^n)", "omega": "Ω(2^n)"}

    await cache.set(cache_key, data, cache_type=CacheKey.ANALYSIS)
    console.print("  [green]✓ Datos almacenados[/green]")

    # 3. Recuperar
    console.print("\n[bold]3. Recuperando del caché:[/bold]")
    cached_data = await cache.get(cache_key)

    if cached_data:
        console.print("  [green]✓ Cache HIT[/green]")
        console.print(f"  Datos: {cached_data}")
    else:
        console.print("  [red]✗ Cache MISS[/red]")

    # 4. Estadísticas
    console.print("\n[bold]4. Estadísticas del caché:[/bold]")
    stats = cache.get_statistics()

    table = Table()
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="magenta")

    for key, value in stats.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)

    # 5. Limpiar
    console.print("\n[bold]5. Limpiando caché:[/bold]")
    count = await cache.clear()
    console.print(f"  [yellow]Eliminadas {count} entradas[/yellow]")

async def demo_complete_workflow():
    """Demo: Workflow completo integrando todos los servicios"""
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold yellow]Demo: Workflow Completo[/bold yellow]",
        border_style="yellow"
    ))

    code = SAMPLE_ALGORITHMS["binary_search"]

    console.print("\n[bold cyan]Flujo completo:[/bold cyan]")
    console.print("  1. Validar código")
    console.print("  2. Verificar caché")
    console.print("  3. Ejecutar análisis")
    console.print("  4. Almacenar en caché")
    console.print("  5. Guardar algoritmo")
    console.print("  6. Exportar resultados")

    # 1. Validar
    console.print("\n[bold]→ Paso 1: Validando...[/bold]")
    validator = ValidationService()
    validation = await validator.validate(
        ValidationRequest(code=code, level=ValidationLevel.COMPLETE)
    )

    if not validation.is_valid:
        console.print("[red]✗ Código inválido, abortando[/red]")
        return

    console.print("[green]✓ Código válido[/green]")

    # 2. Verificar caché
    console.print("\n[bold]→ Paso 2: Verificando caché...[/bold]")
    cache = CacheService()
    cache_key = generate_cache_key(CacheKey.ANALYSIS, code)
    cached = await cache.get(cache_key)

    if cached:
        console.print("[yellow]⚡ Resultado encontrado en caché[/yellow]")
        return

    console.print("[dim]Cache MISS, continuando análisis[/dim]")

    # 3. Analizar
    console.print("\n[bold]→ Paso 3: Ejecutando análisis...[/bold]")
    orchestrator = AnalysisOrchestrator()
    result = await orchestrator.analyze_complete(
        CompleteAnalysisRequest(code=code, generate_visualizations=False)
    )

    console.print(f"[green]✓ Análisis completado en {result.total_duration:.2f}s[/green]")

    # 4. Cachear
    console.print("\n[bold]→ Paso 4: Almacenando en caché...[/bold]")
    await cache.set(cache_key, result.complexity_result, cache_type=CacheKey.ANALYSIS)
    console.print("[green]✓ Resultado cacheado[/green]")

    # 5. Guardar algoritmo
    console.print("\n[bold]→ Paso 5: Guardando algoritmo...[/bold]")
    algo_service = AlgorithmService()
    stored = await algo_service.create(
        AlgorithmCreateRequest(
            code=code,
            name=result.algorithm_name,
            category=AlgorithmCategory.SEARCHING
        )
    )
    console.print(f"[green]✓ Algoritmo guardado (ID: {stored.metadata.id[:8]}...)[/green]")

    # 6. Exportar
    console.print("\n[bold]→ Paso 6: Exportando resultados...[/bold]")
    exporter = ExportService()
    export_result = await exporter.export(
        ExportRequest(
            data={
                "algorithm_name": result.algorithm_name,
                "complexity_result": result.complexity_result,
                "summary": result.summary
            },
            format=ExportFormat.MARKDOWN,
            filename=f"{result.algorithm_name}_report.md"
        )
    )

    if export_result.success:
        console.print(f"[green]✓ Reporte exportado: {export_result.file_path}[/green]")

    console.print("\n[bold green]✓ Workflow completado exitosamente[/bold green]")

# Main
async def main():
    """Ejecutar todos los demos"""
    console.print(Panel.fit(
        "[bold magenta]Demo Completo - Módulo de Servicios[/bold magenta]\n"
        "[dim]Complejity Analyzer - Módulo 5[/dim]",
        border_style="magenta"
    ))

    try:
        # Demo 1: AlgorithmService
        algo = await demo_algorithm_service()

        # Demo 2: ValidationService
        await demo_validation_service()

        # Demo 3: AnalysisOrchestrator
        analysis_result = await demo_analysis_orchestrator()

        # Demo 4: ExportService
        await demo_export_service(analysis_result)

        # Demo 5: CacheService
        await demo_cache_service()

        # Demo 6: Workflow completo
        await demo_complete_workflow()

        console.print("\n" + "="*80)
        console.print(Panel.fit(
            "[bold green]✓ Todos los demos completados[/bold green]",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())