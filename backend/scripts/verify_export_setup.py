#!/usr/bin/env python3
"""
Script de Verificación - Sistema de Exportación

Verifica que todos los componentes del sistema de exportación
estén correctamente instalados y configurados.

Uso:
    python scripts/verify_export_setup.py
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def check_imports():
    """Verifica que todos los imports necesarios funcionen"""
    console.print("\n[bold cyan]1. Verificando Imports...[/bold cyan]")
    
    checks = []
    
    # Core imports
    try:
        from app.core.config import settings
        checks.append(("app.core.config", True, "✓"))
    except ImportError as e:
        checks.append(("app.core.config", False, str(e)))
    
    # Export infrastructure
    try:
        from app.infrastructure.export import (
            ExportFormat,
            ExporterFactory,
            export_analysis,
            PDF_AVAILABLE,
            EXCEL_AVAILABLE
        )
        checks.append(("app.infrastructure.export", True, "✓"))
    except ImportError as e:
        checks.append(("app.infrastructure.export", False, str(e)))
    
    # API endpoints
    try:
        from app.api.v1.endpoints import export
        checks.append(("app.api.v1.endpoints.export", True, "✓"))
    except ImportError as e:
        checks.append(("app.api.v1.endpoints.export", False, str(e)))
    
    # Database models
    try:
        from app.infrastructure.database.models.mongo import (
            Algorithm,
            AnalysisResult,
            PatternDetection
        )
        checks.append(("Database models", True, "✓"))
    except ImportError as e:
        checks.append(("Database models", False, str(e)))
    
    # Rich (for scripts)
    try:
        import rich
        checks.append(("rich", True, "✓"))
    except ImportError as e:
        checks.append(("rich", False, "pip install rich"))
    
    # httpx (for API tests)
    try:
        import httpx
        checks.append(("httpx", True, "✓"))
    except ImportError as e:
        checks.append(("httpx", False, "pip install httpx"))
    
    # Display results
    table = Table(title="Import Check")
    table.add_column("Módulo", style="cyan")
    table.add_column("Estado", style="green", justify="center")
    table.add_column("Nota", style="yellow")
    
    all_ok = True
    for module, success, note in checks:
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        table.add_row(module, status, note)
        if not success:
            all_ok = False
    
    console.print(table)
    return all_ok

def check_export_formats():
    """Verifica formatos de exportación disponibles"""
    console.print("\n[bold cyan]2. Verificando Formatos de Exportación...[/bold cyan]")
    
    try:
        from app.infrastructure.export import (
            ExporterFactory,
            PDF_AVAILABLE,
            EXCEL_AVAILABLE
        )
        
        available = ExporterFactory.get_available_formats()
        
        table = Table(title="Formatos Disponibles")
        table.add_column("Formato", style="cyan")
        table.add_column("Disponible", style="green", justify="center")
        table.add_column("Notas", style="yellow")
        
        # Formatos esperados
        expected = {
            "json": (True, "Core - Siempre disponible"),
            "markdown": (True, "Core - Siempre disponible"),
            "html": (True, "Core - Siempre disponible"),
            "csv": (True, "Core - Siempre disponible"),
            "dot": (True, "Core - Graphviz"),
            "mermaid": (True, "Core - Mermaid diagrams"),
            "svg": (True, "Core - SVG graphics"),
            "pdf": (PDF_AVAILABLE, "Requiere: pip install reportlab" if not PDF_AVAILABLE else "✓"),
            "excel": (EXCEL_AVAILABLE, "Requiere: pip install openpyxl" if not EXCEL_AVAILABLE else "✓"),
        }
        
        all_ok = True
        for format_name, (should_be_available, note) in expected.items():
            from app.infrastructure.export import ExportFormat
            format_enum = ExportFormat(format_name)
            is_available = format_enum in available
            
            status = "[green]✓[/green]" if is_available else "[red]✗[/red]"
            table.add_row(format_name.upper(), status, note)
            
            if should_be_available and not is_available:
                all_ok = False
        
        console.print(table)
        return all_ok
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return False

def check_directories():
    """Verifica que los directorios necesarios existan"""
    console.print("\n[bold cyan]3. Verificando Directorios...[/bold cyan]")
    
    try:
        from app.core.config import settings
        
        dirs_to_check = [
            ("STORAGE_PATH", settings.STORAGE_PATH),
            ("EXPORTS_PATH", settings.EXPORTS_PATH),
            ("ALGORITHMS_PATH", settings.ALGORITHMS_PATH),
            ("TEMP_PATH", settings.TEMP_PATH),
            ("LOG_FILE_PATH parent", settings.LOG_FILE_PATH.parent),
        ]
        
        table = Table(title="Directorios del Sistema")
        table.add_column("Directorio", style="cyan")
        table.add_column("Existe", style="green", justify="center")
        table.add_column("Path", style="white")
        
        all_ok = True
        for name, path in dirs_to_check:
            exists = path.exists()
            status = "[green]✓[/green]" if exists else "[red]✗[/red]"
            table.add_row(name, status, str(path))
            
            if not exists:
                all_ok = False
                # Intentar crear
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    console.print(f"[yellow]→[/yellow] Creado: {path}")
                except Exception as e:
                    console.print(f"[red]✗[/red] No se pudo crear {path}: {e}")
        
        console.print(table)
        return all_ok
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return False

def check_configuration():
    """Verifica la configuración del sistema"""
    console.print("\n[bold cyan]4. Verificando Configuración...[/bold cyan]")
    
    try:
        from app.core.config import settings
        
        table = Table(title="Configuración")
        table.add_column("Variable", style="cyan")
        table.add_column("Valor", style="white")
        table.add_column("Estado", style="green")
        
        configs = [
            ("APP_NAME", settings.APP_NAME, "info"),
            ("APP_VERSION", settings.APP_VERSION, "info"),
            ("APP_ENV", settings.APP_ENV, "info"),
            ("DEBUG", str(settings.DEBUG), "info"),
            ("HOST", settings.HOST, "info"),
            ("PORT", str(settings.PORT), "info"),
            ("DATABASE_TYPE", settings.DATABASE_TYPE, "info"),
            ("ANTHROPIC_API_KEY", "✓ Configurada" if settings.ANTHROPIC_API_KEY else "✗ No configurada", "warning" if not settings.ANTHROPIC_API_KEY else "ok"),
            ("GOOGLE_API_KEY", "✓ Configurada" if settings.GOOGLE_API_KEY else "✗ No configurada", "warning" if not settings.GOOGLE_API_KEY else "ok"),
        ]
        
        all_ok = True
        for var, value, status_type in configs:
            if status_type == "warning" and "✗" in value:
                status = "[yellow]⚠[/yellow]"
                all_ok = False
            elif status_type == "error":
                status = "[red]✗[/red]"
                all_ok = False
            else:
                status = "[green]✓[/green]"
            
            table.add_row(var, value, status)
        
        console.print(table)
        
        if not all_ok:
            console.print("\n[yellow]⚠ Advertencias:[/yellow]")
            console.print("  - Algunas APIs de LLM no están configuradas")
            console.print("  - Configúralas en el archivo .env si las necesitas")
        
        return True  # No es crítico
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return False

def check_optional_dependencies():
    """Verifica dependencias opcionales"""
    console.print("\n[bold cyan]5. Verificando Dependencias Opcionales...[/bold cyan]")
    
    optional_deps = [
        ("reportlab", "Exportación PDF", "pip install reportlab"),
        ("openpyxl", "Exportación Excel", "pip install openpyxl"),
        ("graphviz", "Visualización DOT", "pip install graphviz"),
        ("cairosvg", "Renderizado SVG", "pip install cairosvg"),
    ]
    
    table = Table(title="Dependencias Opcionales")
    table.add_column("Paquete", style="cyan")
    table.add_column("Uso", style="white")
    table.add_column("Estado", style="green", justify="center")
    table.add_column("Instalación", style="yellow")
    
    for package, usage, install_cmd in optional_deps:
        try:
            __import__(package)
            status = "[green]✓[/green]"
            install_info = "Instalado"
        except ImportError:
            status = "[yellow]○[/yellow]"
            install_info = install_cmd
        
        table.add_row(package, usage, status, install_info)
    
    console.print(table)
    console.print("\n[dim]Nota: Las dependencias opcionales no son requeridas para funcionamiento básico[/dim]")
    return True

def check_api_router():
    """Verifica que el router de la API incluya export"""
    console.print("\n[bold cyan]6. Verificando Router de API...[/bold cyan]")
    
    try:
        from app.api.v1.router import api_router
        
        # Verificar que export esté incluido
        routes = []
        for route in api_router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        export_routes = [r for r in routes if '/export' in r]
        
        if export_routes:
            console.print(f"[green]✓[/green] Router incluye {len(export_routes)} rutas de export:")
            for route in export_routes[:5]:  # Mostrar primeras 5
                console.print(f"  [cyan]→[/cyan] {route}")
            return True
        else:
            console.print("[red]✗[/red] No se encontraron rutas de export en el router")
            console.print("[yellow]⚠[/yellow] Asegúrate de que router.py incluya:")
            console.print("    api_router.include_router(export.router, prefix='/export')")
            return False
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return False

def print_summary(results: dict):
    """Imprime resumen final"""
    console.print("\n" + "="*60)
    
    all_ok = all(results.values())
    
    if all_ok:
        panel = Panel.fit(
            "[bold green]Verificación Completa - Todo OK[/bold green]\n\n"
            "[white]El sistema de exportación está correctamente instalado.[/white]\n"
            "[white]Puedes ejecutar:[/white]\n"
            "  [cyan]python scripts/test_api_export.py[/cyan]\n"
            "  [cyan]python scripts/demo_export.py[/cyan]",
            border_style="green"
        )
    else:
        failed = [name for name, ok in results.items() if not ok]
        panel = Panel.fit(
            "[bold red]Verificación Incompleta[/bold red]\n\n"
            f"[white]Problemas encontrados en:[/white]\n" +
            "\n".join(f"  [red]✗[/red] {name}" for name in failed) +
            "\n\n[yellow]Revisa los mensajes anteriores para más detalles[/yellow]",
            border_style="red"
        )
    
    console.print(panel)

def main():
    """Ejecuta todas las verificaciones"""
    console.print(Panel.fit(
        "[bold yellow]Verificación del Sistema de Exportación[/bold yellow]\n"
        "[dim]Comprobando instalación y configuración[/dim]",
        border_style="cyan"
    ))
    
    results = {}
    
    # Ejecutar verificaciones
    results["Imports"] = check_imports()
    results["Formatos"] = check_export_formats()
    results["Directorios"] = check_directories()
    results["Configuración"] = check_configuration()
    results["Dependencias Opcionales"] = check_optional_dependencies()
    results["Router API"] = check_api_router()
    
    # Resumen
    print_summary(results)
    
    # Return code
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]Verificación interrumpida por el usuario[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)