"""
Demo - API de Detección de Patrones

Script de demostración para mostrar cómo usar la API de patrones.
"""

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box

console = Console()

# Base URL de la API
BASE_URL = "http://localhost:8000/api/v1"

ALGORITHMS = {
    "bubble_sort": """
algorithm bubbleSort(A[n])
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
end
""",
    "fibonacci_recursive": """
algorithm fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end
    prev := n - 1
    prev2 := n - 2
    a := fibonacci(prev)
    b := fibonacci(prev2)
    return a + b
end
""",
    "merge_sort": """
algorithm mergeSort(A[n])
begin
    if (n > 1) then
    begin
        mid := n / 2
        call mergeSort(A)
        call mergeSort(A)
        call merge(A, 1, mid, n)
    end
end
""",
    "fibonacci_dp": """
algorithm fibonacciDP(n)
begin
    dp[0] := 0
    dp[1] := 1
    
    for i := 2 to n do
    begin
        prev := i - 1
        prev2 := i - 2
        dp[i] := dp[prev] + dp[prev2]
    end
    
    return dp[n]
end
""",
    "dijkstra": """
algorithm dijkstra(G, start, n)
begin
    for i := 1 to n do
    begin
        dist[i] := 99999
        visited[i] := false
    end
    
    dist[start] := 0
    
    for i := 1 to n do
    begin
        u := findMin(dist)
        visited[u] := true
        
        for v := 1 to n do
        begin
            newDist := dist[u] + weight[u]
            if (visited[v] = false and newDist < dist[v]) then
            begin
                dist[v] := newDist
            end
        end
    end
end
"""
}

def print_header(title: str):
    """Imprime un header bonito"""
    console.print(f"[bold yellow]{title.center(80)}[/bold yellow]")

def print_algorithm(name: str, code: str):
    """Imprime el código del algoritmo"""
    console.print(Panel(
        Syntax(code.strip(), "text", theme="monokai", line_numbers=True),
        title=f"[bold green]Algoritmo: {name}[/bold green]",
        border_style="green"
    ))

def print_pattern_result(data: dict):
    """Imprime el resultado de la detección de patrones"""
    # Patrón primario
    if data.get("primary_pattern"):
        primary = data["primary_pattern"]
        console.print(Panel(
            f"[bold]{primary['pattern_name']}[/bold]\n\n"
            f"Tipo: {primary['pattern_type']}\n"
            f"Confianza: {primary['confidence']:.2%} ({primary['confidence_level']})\n"
            f"Score Final: {primary['final_score']:.2%}\n"
            f"Complejidad Típica: {primary['typical_complexity']}\n\n"
            f"[italic]{primary['reasoning']}[/italic]",
            title="[bold magenta]Patrón Principal[/bold magenta]",
            border_style="magenta"
        ))

    # Tabla de todos los patrones
    if data.get("all_patterns"):
        table = Table(
            title="Todos los Patrones Detectados",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        table.add_column("Rank", style="dim", width=6)
        table.add_column("Patrón", style="green")
        table.add_column("Confianza", justify="right")
        table.add_column("Score Final", justify="right")
        table.add_column("Nivel", style="yellow")

        for pattern in data["all_patterns"]:
            rank_str = f"#{pattern['rank']}"
            if pattern['is_primary']:
                rank_str += "LEAD"

            conf_color = "green" if pattern['confidence'] >= 0.7 else "yellow" if pattern['confidence'] >= 0.5 else "red"
            table.add_row(
                rank_str,
                pattern['pattern_name'],
                f"[{conf_color}]{pattern['confidence']:.2%}[/{conf_color}]",
                f"{pattern['final_score']:.2%}",
                pattern['confidence_level']
            )

        console.print(table)

    # Indicadores del patrón principal
    if data.get("primary_pattern"):
        primary = data["primary_pattern"]

        # Indicadores encontrados
        if primary.get("indicators_found"):
            console.print("\n[bold green]Indicadores Encontrados:[/bold green]")
            for ind in primary["indicators_found"]:
                evidence = f" - {ind['evidence']}" if ind.get('evidence') else ""
                console.print(f"  • {ind['name']}: {ind['description']}{evidence}")
    
        # Indicadores faltantes
        if primary.get("indicators_missing"):
            console.print("\n[bold red]Indicadores Faltantes:[/bold red]")
            for ind in primary["indicators_missing"]:
                console.print(f"  • {ind['name']}: {ind['description']}")

    # Resumen
    if data.get("summary"):
        console.print(Panel(
            data["summary"],
            title="[bold blue]Resumen[/bold blue]",
            border_style="blue"
        ))

def demo_detect_all_patterns(algo_name: str):
    """Demo: Detectar todos los patrones"""
    print_header(f"DEMO 1: Detectar Todos los Patrones - {algo_name}")

    code = ALGORITHMS[algo_name]
    print_algorithm(algo_name, code)

    console.print("\n[bold]Enviando request a /patterns/detect...[/bold]")

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{BASE_URL}/patterns/detect",
            json={
                "code": code,
                "min_confidence": 0.3
            }
        )

    if response.status_code == 200:
        data = response.json()
        console.print("[bold green]✓ Respuesta exitosa[/bold green]\n")
        print_pattern_result(data)
    else:
        console.print(f"[bold red]✗ Error: {response.status_code}[/bold red]")
        console.print(response.text)

def demo_detect_specific_pattern(algo_name: str, pattern_type: str):
    """Demo: Detectar patrón específico"""
    print_header(f"DEMO 2: Detectar Patrón Específico - {pattern_type}")

    code = ALGORITHMS[algo_name]
    print_algorithm(algo_name, code)

    console.print(f"\n[bold]Detectando patrón específico: {pattern_type}...[/bold]")

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{BASE_URL}/patterns/detect-specific",
            json={
                "code": code,
                "pattern_type": pattern_type
            }
        )

    if response.status_code == 200:
        data = response.json()
        console.print("[bold green]OK - Respuesta exitosa[/bold green]\n")

        if data["pattern_detected"]:
            pattern = data["pattern_info"]
            console.print(Panel(
                f"[bold]{pattern['pattern_name']}[/bold]\n\n"
                f"Confianza: {pattern['confidence']:.2%}\n"
                f"Nivel: {pattern['confidence_level']}\n\n"
                f"{pattern['reasoning']}",
                title="[bold green]Patron Detectado[/bold green]",
                border_style="green"
            ))
        else:
            console.print("[yellow]ADVERTENCIA: Patron no detectado[/yellow]")
    else:
        console.print(f"[bold red]ERROR: {response.status_code}[/bold red]")

def demo_available_patterns():
    """Demo: Listar patrones disponibles"""
    print_header("DEMO 3: Patrones Disponibles")

    console.print("[bold]Consultando /patterns/available...[/bold]\n")

    with httpx.Client(timeout=30.0) as client:
        response = client.get(f"{BASE_URL}/patterns/available")

    if response.status_code == 200:
        data = response.json()
        console.print(f"[bold green]OK - {data['total']} patrones disponibles[/bold green]\n")

        table = Table(
            title="Patrones Disponibles",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        table.add_column("Tipo", style="cyan")
        table.add_column("Nombre", style="green")
        table.add_column("Descripción", style="white")
        table.add_column("Complejidad", style="yellow")

        for pattern in data["patterns"]:
            table.add_row(
                pattern["type"],
                pattern["name"],
                pattern["description"],
                pattern["typical_complexity"]
            )

        console.print(table)
    else:
        console.print(f"[bold red]ERROR: {response.status_code}[/bold red]")

def demo_compare_algorithms():
    """Demo: Comparar múltiples algoritmos"""
    print_header("DEMO 4: Comparación de Algoritmos")

    algorithms = ["bubble_sort", "merge_sort", "fibonacci_dp"]
    results = []

    for algo_name in algorithms:
        console.print(f"\n[bold]Analizando {algo_name}...[/bold]")

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{BASE_URL}/patterns/detect",
                json={
                    "code": ALGORITHMS[algo_name],
                    "min_confidence": 0.3
                }
            )

        if response.status_code == 200:
            data = response.json()
            primary = data.get("primary_pattern")
            if primary:
                results.append({
                    "name": algo_name,
                    "primary": primary.get("pattern_name", "N/A"),
                    "confidence": primary.get("confidence", 0),
                    "complexity": primary.get("typical_complexity", "N/A")
                })
            else:
                # Patrón no detectado (posible bug de 'children' en ast_nodes)
                results.append({
                    "name": algo_name,
                    "primary": "(Sin detectar)",
                    "confidence": 0,
                    "complexity": "N/A"
                })
                console.print(f"[yellow]ADVERTENCIA: Sin patron detectado para {algo_name}[/yellow]")
        else:
            console.print(f"[red]ERROR {response.status_code} para {algo_name}[/red]")
            results.append({
                "name": algo_name,
                "primary": f"Error {response.status_code}",
                "confidence": 0,
                "complexity": "N/A"
            })

    # Tabla comparativa
    table = Table(
        title="Comparación de Algoritmos",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Algoritmo", style="green")
    table.add_column("Patrón Principal", style="yellow")
    table.add_column("Confianza", justify="right")
    table.add_column("Complejidad", style="magenta")

    for result in results:
        conf_color = "green" if result["confidence"] >= 0.7 else "yellow"
        table.add_row(
            result["name"],
            result["primary"],
            f"[{conf_color}]{result['confidence']:.2%}[/{conf_color}]",
            result["complexity"]
        )

    console.print("\n")
    console.print(table)

def main():
    """Ejecuta todas las demos"""
    console.print(Panel.fit(
        "[bold magenta]Demo de API de Detección de Patrones[/bold magenta]\n\n"
        "Este script demuestra cómo usar los endpoints de la API\n"
        "para detectar patrones algorítmicos en pseudocódigo.",
        border_style="magenta"
    ))

    try:
        # Demo 1: Detectar todos los patrones en Bubble Sort
        demo_detect_all_patterns("bubble_sort")

        input("\n[Presiona Enter para continuar...]")

        # Demo 2: Detectar patrón específico (recursión en Fibonacci)
        demo_detect_specific_pattern("fibonacci_recursive", "recursive")

        input("\n[Presiona Enter para continuar...]")

        # Demo 3: Listar patrones disponibles
        demo_available_patterns()

        input("\n[Presiona Enter para continuar...]")

        # Demo 4: Comparar múltiples algoritmos
        demo_compare_algorithms()

        console.print("\n[bold green]Demos completadas exitosamente![/bold green]")

    except httpx.ConnectError:
        console.print("\n[bold red]ERROR: No se pudo conectar al servidor[/bold red]")
        console.print("[yellow]Asegúrate de que el servidor esté corriendo en http://localhost:8000[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]ERROR: {e}[/bold red]")

if __name__ == "__main__":
    main()