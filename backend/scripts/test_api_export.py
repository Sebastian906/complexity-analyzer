"""
Script para probar los endpoints de exportación de la API.

Ejecuta requests de ejemplo contra los endpoints de export.

Uso:
    python scripts/test_api_export.py
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import httpx
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.core.config import settings

console = Console()

# Fix: usar localhost en lugar de 0.0.0.0 para conexión desde cliente
BASE_URL = f"http://127.0.0.1:{settings.PORT}"

def check_server():
    """Verifica que el servidor esté corriendo"""
    console.print("\n[bold cyan]Verificando servidor...[/bold cyan]")
    
    try:
        response = httpx.get(f"{BASE_URL}/", timeout=5.0)
        if response.status_code == 200:
            console.print("[green]✓[/green] Servidor accesible")
            data = response.json()
            console.print(f"[cyan]API:[/cyan] {data.get('name', 'N/A')}")
            console.print(f"[cyan]Version:[/cyan] {data.get('version', 'N/A')}")
            console.print(f"[cyan]Status:[/cyan] {data.get('status', 'N/A')}")
            return True
        else:
            console.print(f"[red]✗[/red] Servidor respondió con código: {response.status_code}")
            return False
    except httpx.ConnectError:
        console.print("[red]✗[/red] No se pudo conectar al servidor")
        console.print("[yellow]Asegúrate de ejecutar:[/yellow]")
        console.print("  python scripts/run_dev.py")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return False

def test_get_formats():
    """Test: Obtener formatos disponibles"""
    console.print("\n[bold cyan]Test 1: GET /api/v1/export/formats[/bold cyan]")
    
    try:
        response = httpx.get(f"{BASE_URL}/api/v1/export/formats", timeout=10.0)
        
        if response.status_code == 200:
            console.print("[green]✓[/green] Formatos obtenidos exitosamente")
            data = response.json()
            
            # Tabla de formatos disponibles
            table = Table(title="Formatos de Exportación")
            table.add_column("Formato", style="cyan")
            table.add_column("Disponible", style="green")
            table.add_column("Nota", style="yellow")
            
            formats = data.get("formats", {})
            available = formats.get("available", [])
            all_formats = formats.get("all", [])
            optional = formats.get("optional_dependencies", {})
            
            for fmt in all_formats:
                is_available = fmt in available
                status = "✓" if is_available else "✗"
                
                note = ""
                if fmt in optional:
                    opt_data = optional[fmt]
                    if not opt_data.get("available", False):
                        note = f"Requiere: {opt_data.get('package', 'N/A')}"
                
                table.add_row(fmt.upper(), status, note)
            
            console.print(table)
            return True
        else:
            console.print(f"[red]✗[/red] Error: {response.status_code}")
            console.print(response.text[:200])
            return False
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return False

def test_analyze_algorithm():
    """Test: Analizar un algoritmo (prerequisito para exportar)"""
    console.print("\n[bold cyan]Test 2: Analizar Algoritmo[/bold cyan]")
    
    algorithm_code = """algorithm binary_search(A[1..n], x)
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
end"""
    
    console.print("[dim]Código del algoritmo:[/dim]")
    syntax = Syntax(algorithm_code, "text", theme="monokai", line_numbers=True)
    console.print(syntax)
    
    try:
        with console.status("[cyan]Analizando..."):
            response = httpx.post(
                f"{BASE_URL}/api/v1/analysis/analyze",
                json={
                    "code": algorithm_code,
                    "analyze_temporal": True,
                    "analyze_spatial": True,
                    "detect_patterns": True
                },
                timeout=30.0
            )
        
        if response.status_code == 200:
            console.print("[green]✓[/green] Análisis completado")
            data = response.json()
            
            # Tabla de resultados
            table = Table(title="Resultados del Análisis")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="magenta")
            
            table.add_row("Success", str(data.get("success", "N/A")))
            table.add_row("Algorithm ID", str(data.get("algorithm_id", "N/A")))
            table.add_row("Algorithm Name", data.get("algorithm_name", "N/A"))
            table.add_row("Big O", data.get("big_o", "N/A"))
            table.add_row("Omega", data.get("omega", "N/A"))
            table.add_row("Theta", data.get("theta", "N/A"))
            table.add_row("Space", data.get("spatial_complexity", "N/A"))
            table.add_row("Primary Pattern", data.get("primary_technique", "N/A"))
            
            console.print(table)
            
            return data.get("algorithm_id")
        else:
            console.print(f"[red]✗[/red] Error: {response.status_code}")
            console.print(response.text[:500])
            return None
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return None

def test_export_single(algorithm_id: str, format_type: str = "json"):
    """Test: Exportar a un formato específico"""
    console.print(f"\n[bold cyan]Test 3: Exportar a {format_type.upper()}[/bold cyan]")
    
    if not algorithm_id:
        console.print("[red]✗[/red] No hay algorithm_id. Ejecuta el análisis primero.")
        return False
    
    try:
        with console.status(f"[cyan]Exportando a {format_type}..."):
            response = httpx.post(
                f"{BASE_URL}/api/v1/export/export",
                json={
                    "algorithm_id": algorithm_id,
                    "format": format_type,
                    "include_patterns": True,
                    "include_visualizations": True
                },
                timeout=30.0
            )
        
        if response.status_code == 200:
            console.print(f"[green]✓[/green] Exportado a {format_type.upper()}")
            data = response.json()
            
            table = Table(title=f"Exportación {format_type.upper()}")
            table.add_column("Campo", style="cyan")
            table.add_column("Valor", style="white")
            
            table.add_row("Success", str(data.get("success")))
            table.add_row("Format", data.get("format", "N/A"))
            table.add_row("File Path", data.get("file_path", "N/A"))
            
            file_size = data.get("file_size_bytes")
            if file_size:
                size_kb = file_size / 1024
                table.add_row("File Size", f"{file_size:,} bytes ({size_kb:.2f} KB)")
            
            table.add_row("Download URL", data.get("download_url", "N/A"))
            
            console.print(table)
            
            # Mostrar contenido si es formato de texto
            if format_type in ["json", "markdown"] and data.get("content"):
                console.print(f"\n[dim]Preview del contenido ({format_type}):[/dim]")
                preview = data["content"][:500] + "..." if len(data["content"]) > 500 else data["content"]
                
                if format_type == "json":
                    try:
                        formatted = json.dumps(json.loads(data["content"]), indent=2)
                        syntax = Syntax(formatted[:500], "json", theme="monokai")
                        console.print(syntax)
                    except:
                        console.print(preview)
                else:
                    console.print(preview)
            
            return data.get("file_path")
        else:
            console.print(f"[red]✗[/red] Error: {response.status_code}")
            console.print(response.text[:500])
            return None
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return None

def test_export_multiple(algorithm_id: str):
    """Test: Exportar a múltiples formatos"""
    console.print("\n[bold cyan]Test 4: Exportar a Múltiples Formatos[/bold cyan]")
    
    if not algorithm_id:
        console.print("[red]✗[/red] No hay algorithm_id. Ejecuta el análisis primero.")
        return False
    
    formats = ["json", "markdown", "html", "csv"]
    console.print(f"[dim]Formatos seleccionados: {', '.join(formats)}[/dim]")
    
    try:
        with console.status("[cyan]Exportando a múltiples formatos..."):
            response = httpx.post(
                f"{BASE_URL}/api/v1/export/export/multiple",
                json={
                    "algorithm_id": algorithm_id,
                    "formats": formats,
                    "include_patterns": True,
                    "include_visualizations": False
                },
                timeout=60.0
            )
        
        if response.status_code == 200:
            console.print("[green]✓[/green] Exportación múltiple completada")
            data = response.json()
            
            # Resumen
            console.print(f"\n[cyan]Total:[/cyan] {data.get('total_files', 0)} formatos")
            console.print(f"[green]Exitosos:[/green] {data.get('successful', 0)}")
            console.print(f"[red]Fallidos:[/red] {data.get('failed', 0)}")
            
            # Tabla de resultados por formato
            table = Table(title="Resultados por Formato")
            table.add_column("Formato", style="cyan")
            table.add_column("Estado", style="green")
            table.add_column("Archivo", style="white")
            table.add_column("Tamaño", style="yellow")
            
            results = data.get("results", {})
            for format_type, result in results.items():
                status = "✓" if result.get("success") else "✗"
                file_path = result.get("file_path", "N/A")
                file_name = Path(file_path).name if file_path != "N/A" else "N/A"
                
                file_size = result.get("file_size")
                size_str = f"{file_size:,} bytes" if file_size else "N/A"
                
                table.add_row(format_type.upper(), status, file_name, size_str)
            
            console.print(table)
            return True
        else:
            console.print(f"[red]✗[/red] Error: {response.status_code}")
            console.print(response.text[:500])
            return False
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return False

def test_download(file_path: str):
    """Test: Descargar archivo exportado"""
    console.print("\n[bold cyan]Test 5: Descargar Archivo[/bold cyan]")
    
    if not file_path:
        console.print("[yellow]⚠[/yellow] No hay archivo para descargar. Omitiendo test.")
        return True
    
    filename = Path(file_path).name
    console.print(f"[dim]Archivo: {filename}[/dim]")
    
    try:
        with console.status(f"[cyan]Descargando {filename}..."):
            response = httpx.get(
                f"{BASE_URL}/api/v1/export/download/{filename}",
                timeout=30.0
            )
        
        if response.status_code == 200:
            console.print(f"[green]✓[/green] Archivo descargado")
            
            # Guardar en directorio temporal
            download_dir = Path("./test_downloads")
            download_dir.mkdir(exist_ok=True)
            
            output_path = download_dir / filename
            output_path.write_bytes(response.content)
            
            console.print(f"[cyan]Guardado en:[/cyan] {output_path}")
            console.print(f"[cyan]Tamaño:[/cyan] {len(response.content):,} bytes")
            return True
        else:
            console.print(f"[red]✗[/red] Error: {response.status_code}")
            console.print(response.text[:200])
            return False
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return False

def test_cleanup():
    """Test: Limpiar archivos antiguos"""
    console.print("\n[bold cyan]Test 6: Limpiar Archivos Antiguos[/bold cyan]")
    
    older_than_days = 30
    console.print(f"[dim]Eliminando archivos más antiguos que {older_than_days} días[/dim]")
    
    try:
        with console.status("[cyan]Limpiando..."):
            response = httpx.delete(
                f"{BASE_URL}/api/v1/export/cleanup",
                params={"older_than_days": older_than_days},
                timeout=30.0
            )
        
        if response.status_code == 200:
            console.print("[green]✓[/green] Limpieza completada")
            data = response.json()
            
            table = Table(title="Resultados de Limpieza")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="white")
            
            table.add_row("Success", str(data.get("success")))
            table.add_row("Archivos eliminados", str(data.get("deleted_files", 0)))
            table.add_row("Bytes liberados", f"{data.get('deleted_size_bytes', 0):,}")
            table.add_row("MB liberados", str(data.get("deleted_size_mb", 0)))
            table.add_row("Cutoff (días)", str(data.get("cutoff_days")))
            
            console.print(table)
            return True
        else:
            console.print(f"[red]✗[/red] Error: {response.status_code}")
            console.print(response.text[:200])
            return False
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        return False

def main():
    """Ejecuta todos los tests"""
    console.print(Panel.fit(
        "[bold yellow]Test Suite - Endpoints de Exportación[/bold yellow]\n"
        f"[cyan]Base URL: {BASE_URL}[/cyan]",
        border_style="cyan"
    ))
    
    # Verificar servidor
    if not check_server():
        return
    
    # Variables para tracking
    algorithm_id = None
    export_file_path = None
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Formatos disponibles
    if test_get_formats():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 2: Analizar algoritmo
    algorithm_id = test_analyze_algorithm()
    if algorithm_id:
        tests_passed += 1
    else:
        tests_failed += 1
        console.print("\n[red]Tests subsecuentes omitidos (no hay algorithm_id)[/red]")
        print_summary(tests_passed, tests_failed)
        return
    
    # Test 3: Exportar a JSON
    export_file_path = test_export_single(algorithm_id, "json")
    if export_file_path:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 4: Exportación múltiple
    if test_export_multiple(algorithm_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 5: Descargar archivo
    if test_download(export_file_path):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 6: Cleanup
    if test_cleanup():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Resumen
    print_summary(tests_passed, tests_failed)

def print_summary(passed: int, failed: int):
    """Imprime resumen de tests"""
    total = passed + failed
    
    console.print("\n" + "="*50)
    console.print(Panel.fit(
        f"[bold]Resumen de Tests[/bold]\n\n"
        f"[green]Exitosos:[/green] {passed}/{total}\n"
        f"[red]Fallidos:[/red] {failed}/{total}\n"
        f"[cyan]Total:[/cyan] {total}",
        border_style="cyan" if failed == 0 else "red"
    ))
    
    if failed == 0:
        console.print("\n[bold green]¡Todos los tests pasaron![/bold green]")
    else:
        console.print("\n[bold red]Algunos tests fallaron[/bold red]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrumpidos por el usuario[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error general: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()