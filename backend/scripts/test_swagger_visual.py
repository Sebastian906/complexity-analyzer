
"""
Script para probar visualmente el funcionamiento del API con ejemplos interactivos

Ejecutar el servidor primero:
    python scripts/run_dev.py

Luego ejecutar este script en otra terminal:
    python scripts/test_swagger_visual.py
"""

import httpx
import json
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress
import time

console = Console()


def normalize_complexity(notation: str) -> str:
    """
    Normaliza una notación de complejidad para comparación.
    Convierte diferentes representaciones equivalentes a un formato común.
    
    Ejemplos:
        - "O(n²)" -> "O(n^2)"
        - "O(n³)" -> "O(n^3)"
        - "O(log n)" -> "O(log n)"
        - "Ω(n²)" -> "Ω(n^2)"
    """
    if not notation:
        return ""
    
    result = notation
    
    # Mapeo de superíndices Unicode a formato con ^
    superscript_map = {
        '⁰': '^0',
        '¹': '^1',
        '²': '^2',
        '³': '^3',
        '⁴': '^4',
        '⁵': '^5',
        '⁶': '^6',
        '⁷': '^7',
        '⁸': '^8',
        '⁹': '^9',
    }
    
    for sup, replacement in superscript_map.items():
        result = result.replace(sup, replacement)
    
    # Normalizar espacios
    result = re.sub(r'\s+', ' ', result).strip()
    
    # Normalizar log (log n, log(n), logn -> log n)
    result = re.sub(r'log\s*\(\s*n\s*\)', 'log n', result)
    result = re.sub(r'log\s*n', 'log n', result)
    
    return result


def complexity_matches(expected: str, obtained: str) -> bool:
    """
    Compara dos notaciones de complejidad considerando equivalencias.
    
    Args:
        expected: Notación esperada (ej: "O(n²)")
        obtained: Notación obtenida del analizador (ej: "O(n^2)")
    
    Returns:
        True si son equivalentes, False en caso contrario.
    """
    norm_expected = normalize_complexity(expected)
    norm_obtained = normalize_complexity(obtained)
    
    # Comparación exacta después de normalización
    if norm_expected == norm_obtained:
        return True
    
    # Verificar si una contiene a la otra (para casos como "O(n)" in "O(n) - lineal")
    if norm_expected in norm_obtained or norm_obtained in norm_expected:
        return True
    
    return False

BASE_URL = "http://localhost:8000"

# Algoritmos de prueba con complejidades conocidas
TEST_ALGORITHMS = {
    "1_constante": {
        "name": "Algoritmo Constante O(1)",
        "code": """algorithm constant(n)
begin
    x := 1
    y := 2
    z := x + y
end""",
        "expected": {"big_o": "O(1)", "omega": "Ω(1)", "theta": "Θ(1)"}
    },
    
    "2_lineal": {
        "name": "Búsqueda Lineal O(n)",
        "code": """algorithm linearSearch(A[n], x)
begin
    for i := 1 to n do
    begin
        if (A[i] = x) then
        begin
            return i
        end
    end
    return -1
end""",
        "expected": {"big_o": "O(n)", "omega": "Ω(1)", "theta": "Θ(n)"}
    },
    
    "3_cuadratico": {
        "name": "Bubble Sort O(n²)",
        "code": """algorithm bubbleSort(A[n])
begin
    for i := 1 to n - 1 do
    begin
        for j := 1 to n - i do
        begin
            if (A[j] > A[j + 1]) then
            begin
                temp := A[j]
                A[j] := A[j + 1]
                A[j + 1] := temp
            end
        end
    end
end""",
        "expected": {"big_o": "O(n²)", "omega": "Ω(n²)", "theta": "Θ(n²)"}
    },
    
    "4_logaritmico": {
        "name": "Búsqueda Binaria O(log n)",
        "code": """algorithm binarySearch(A[n], x)
begin
    left := 1
    right := n
    
    while (left <= right) do
    begin
        mid := (left + right) / 2
        
        if (A[mid] = x) then
        begin
            return mid
        end
        
        if (A[mid] < x) then
        begin
            left := mid + 1
        end
        else
        begin
            right := mid - 1
        end
    end
    
    return -1
end""",
        "expected": {"big_o": "O(log n)", "omega": "Ω(1)", "theta": "Θ(log n)"}
    },
    
    "5_condicional": {
        "name": "Complejidad Condicional",
        "code": """algorithm conditional(n, mode)
begin
    if (mode = 1) then
    begin
        for i := 1 to n do
        begin
            for j := 1 to n do
            begin
                x := x + 1
            end
        end
    end
    else
    begin
        x := x + 1
    end
end""",
        "expected": {"big_o": "O(n²)", "omega": "Ω(1)", "theta": "depende"}
    }
}

def print_header():
    """Imprime header del programa"""
    console.print(Panel.fit(
        "[bold cyan]ANALIZADOR DE COMPLEJIDAD ALGORÍTMICA[/bold cyan]\n"
        "[yellow]Pruebas Visuales con FastAPI/Swagger[/yellow]",
        border_style="cyan"
    ))

def check_server():
    """Verifica que el servidor esté corriendo"""
    try:
        response = httpx.get(f"{BASE_URL}/", timeout=5.0)
        if response.status_code == 200:
            console.print("[green]✓[/green] Servidor en línea")
            return True
        else:
            console.print(f"[yellow]⚠[/yellow] Servidor responde con código {response.status_code}")
            return True
    except httpx.ConnectError:
        console.print("[red]✗[/red] No se pudo conectar al servidor")
        console.print("\n[yellow]Inicia el servidor primero:[/yellow]")
        console.print("  python scripts/run_dev.py")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        return False

def analyze_algorithm(name: str, code: str, expected: dict):
    """Analiza un algoritmo y muestra resultados"""
    console.print(f"\n[bold cyan]═══ {name} ═══[/bold cyan]")
    
    # Mostrar código
    console.print("\n[bold]Código:[/bold]")
    syntax = Syntax(code, "text", theme="monokai", line_numbers=True)
    console.print(syntax)
    
    # Mostrar complejidad esperada
    console.print("\n[bold]Complejidad Esperada:[/bold]")
    expected_table = Table(show_header=False, box=None)
    expected_table.add_column("Notación", style="cyan")
    expected_table.add_column("Valor", style="yellow")
    for notation, value in expected.items():
        expected_table.add_row(notation, value)
    console.print(expected_table)
    
    # Hacer request
    console.print("\n[bold]Analizando...[/bold]")
    try:
        with Progress() as progress:
            task = progress.add_task("[cyan]Procesando...", total=100)
            
            start_time = time.time()
            response = httpx.post(
                f"{BASE_URL}/api/v1/analysis/analyze",
                json={
                    "code": code,
                    "analyze_temporal": True,
                    "analyze_spatial": True,
                    "analyze_line_by_line": True
                },
                timeout=30.0
            )
            elapsed = time.time() - start_time
            progress.update(task, completed=100)
        
        if response.status_code == 200:
            data = response.json()
            
            # Mostrar resultados
            console.print("\n[bold green]✓ Análisis Completado[/bold green]")
            console.print(f"[dim]Tiempo: {elapsed:.2f}s[/dim]")
            
            # Tabla de resultados
            results_table = Table(title="Resultados del Análisis", show_header=True)
            results_table.add_column("Campo", style="cyan", width=20)
            results_table.add_column("Valor", style="magenta")
            
            results_table.add_row("Algoritmo", data.get("algorithm_name", "N/A"))
            results_table.add_row("Big O (Peor)", data.get("big_o", "N/A"))
            results_table.add_row("Omega (Mejor)", data.get("omega", "N/A"))
            results_table.add_row("Theta (Promedio)", data.get("theta", "N/A"))
            
            if data.get("metadata"):
                metadata = data["metadata"]
                results_table.add_row("Recursivo", str(metadata.get("is_recursive", False)))
                results_table.add_row("Prof. Máxima", str(metadata.get("max_nesting_depth", 0)))
            
            console.print(results_table)
            
            # Análisis línea por línea
            if data.get("line_by_line"):
                lbl = data["line_by_line"]
                if lbl.get("lines"):
                    console.print("\n[bold]Análisis Línea por Línea:[/bold]")
                    
                    lines_table = Table(show_header=True, title="Ejecuciones por Línea")
                    lines_table.add_column("Línea", justify="right", style="cyan")
                    lines_table.add_column("Tipo", style="yellow")
                    lines_table.add_column("Ejecuciones", style="magenta")
                    lines_table.add_column("Explicación", style="dim")
                    
                    for line_info in lbl["lines"][:10]:  # Mostrar solo primeras 10
                        lines_table.add_row(
                            str(line_info.get("line", "?")),
                            line_info.get("type", "?"),
                            line_info.get("executions", "?"),
                            line_info.get("explanation", "")[:40] + "..."
                        )
                    
                    console.print(lines_table)
            
            # Comparar con esperado
            console.print("\n[bold]Comparación con Esperado:[/bold]")
            compare_table = Table(show_header=True)
            compare_table.add_column("Notación", style="cyan")
            compare_table.add_column("Esperado", style="yellow")
            compare_table.add_column("Obtenido", style="magenta")
            compare_table.add_column("Match", justify="center")
            
            big_o_match = complexity_matches(expected["big_o"], data.get("big_o", ""))
            omega_match = complexity_matches(expected["omega"], data.get("omega", ""))
            
            compare_table.add_row(
                "Big O",
                expected["big_o"],
                data.get("big_o", "N/A"),
                "✓" if big_o_match else "✗"
            )
            compare_table.add_row(
                "Omega",
                expected["omega"],
                data.get("omega", "N/A"),
                "✓" if omega_match else "✗"
            )
            
            console.print(compare_table)
            
        else:
            console.print(f"[red]✗ Error {response.status_code}[/red]")
            console.print(response.text)
    
    except httpx.TimeoutException:
        console.print("[red]✗ Timeout - El análisis tomó demasiado tiempo[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
    
    console.print("\n" + "─" * 80)

def show_api_info():
    """Muestra información de la API"""
    console.print("\n[bold cyan]Información de la API[/bold cyan]")
    
    try:
        # Root endpoint
        response = httpx.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            
            info_table = Table(show_header=False, box=None)
            info_table.add_column("Campo", style="cyan")
            info_table.add_column("Valor", style="yellow")
            
            info_table.add_row("Nombre", data.get("name", "N/A"))
            info_table.add_row("Versión", data.get("version", "N/A"))
            info_table.add_row("Entorno", data.get("environment", "N/A"))
            info_table.add_row("Estado", data.get("status", "N/A"))
            
            console.print(info_table)
        
        # Endpoints disponibles
        response = httpx.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get("paths", {})
            
            console.print("\n[bold]Endpoints Disponibles:[/bold]")
            endpoints_table = Table(show_header=True)
            endpoints_table.add_column("Path", style="cyan")
            endpoints_table.add_column("Métodos", style="yellow")
            
            for path, methods in paths.items():
                method_list = ", ".join([m.upper() for m in methods.keys()])
                endpoints_table.add_row(path, method_list)
            
            console.print(endpoints_table)
    
    except Exception as e:
        console.print(f"[red]Error obteniendo info: {e}[/red]")

def main():
    """Función principal"""
    print_header()
    
    # Verificar servidor
    if not check_server():
        return
    
    # Mostrar info de la API
    show_api_info()
    
    # Links útiles
    console.print("\n[bold cyan]Links Útiles:[/bold cyan]")
    console.print(f"Swagger UI: [link={BASE_URL}/docs]{BASE_URL}/docs[/link]")
    console.print(f"ReDoc: [link={BASE_URL}/redoc]{BASE_URL}/redoc[/link]")
    console.print(f"OpenAPI: [link={BASE_URL}/openapi.json]{BASE_URL}/openapi.json[/link]")
    
    # Menú interactivo
    console.print("\n[bold cyan]Selecciona un algoritmo para probar:[/bold cyan]")
    for key, algo in TEST_ALGORITHMS.items():
        console.print(f"  {key}. {algo['name']}")
    console.print("  0. Probar todos")
    console.print("  q. Salir")
    
    choice = console.input("\n[cyan]Opción:[/cyan] ").strip()
    
    if choice == 'q':
        console.print("[yellow]Saliendo...[/yellow]")
        return
    
    if choice == '0':
        # Probar todos
        for key, algo in TEST_ALGORITHMS.items():
            analyze_algorithm(
                algo["name"],
                algo["code"],
                algo["expected"]
            )
            input("\nPresiona Enter para continuar...")
    else:
        # Probar uno específico
        if choice in TEST_ALGORITHMS:
            algo = TEST_ALGORITHMS[choice]
            analyze_algorithm(
                algo["name"],
                algo["code"],
                algo["expected"]
            )
        else:
            console.print("[red]Opción inválida[/red]")
    
    console.print("\n[bold green]✓ Pruebas completadas[/bold green]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrumpido por el usuario[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error inesperado: {e}[/red]")