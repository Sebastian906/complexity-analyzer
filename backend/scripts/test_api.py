"""
Script para probar la API localmente.

Ejecuta requests de ejemplo contra los endpoints.
"""

import httpx
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


BASE_URL = "http://localhost:8000"


def test_root():
    """Test root endpoint"""
    console.print("\n[bold cyan]Testing Root Endpoint...[/bold cyan]")
    
    response = httpx.get(f"{BASE_URL}/")
    
    if response.status_code == 200:
        console.print("[green]✓[/green] Root endpoint OK")
        data = response.json()
        console.print(f"[cyan]Message:[/cyan] {data.get('message', 'N/A')}")
    else:
        console.print(f"[red]✗[/red] Root failed: {response.status_code}")


def test_docs():
    """Test docs endpoint"""
    console.print("\n[bold cyan]Testing Docs Endpoint...[/bold cyan]")
    
    response = httpx.get(f"{BASE_URL}/docs")
    
    if response.status_code == 200:
        console.print("[green]✓[/green] Swagger docs accessible")
    else:
        console.print(f"[red]✗[/red] Docs failed: {response.status_code}")


def test_analyze():
    """Test analysis endpoint"""
    console.print("\n[bold cyan]Testing Analysis Endpoint...[/bold cyan]")
    
    code = """algorithm test(n)
begin
    for i ← 1 to n do
    begin
        x ← x + 1
    end
end"""
    
    response = httpx.post(
        f"{BASE_URL}/api/v1/analysis/analyze",
        json={
            "code": code,
            "analyze_temporal": True,
            "analyze_spatial": True
        },
        timeout=30.0
    )
    
    if response.status_code == 200:
        console.print("[green]✓[/green] Analysis endpoint responded")
        data = response.json()
        
        table = Table(title="Analysis Response")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Success", str(data.get("success", "N/A")))
        table.add_row("Algorithm Name", data.get("algorithm_name", "N/A"))
        table.add_row("Big O", data.get("big_o", "N/A"))
        table.add_row("Omega", data.get("omega", "N/A"))
        table.add_row("Theta", data.get("theta", "N/A"))
        table.add_row("Message", data.get("message", "N/A"))
        
        console.print(table)
    else:
        console.print(f"[red]✗[/red] Analysis failed: {response.status_code}")
        console.print(response.text)


def test_openapi():
    """Test OpenAPI schema"""
    console.print("\n[bold cyan]Testing OpenAPI Schema...[/bold cyan]")
    
    response = httpx.get(f"{BASE_URL}/openapi.json")
    
    if response.status_code == 200:
        console.print("[green]✓[/green] OpenAPI schema accessible")
        data = response.json()
        console.print(f"[cyan]API Title:[/cyan] {data.get('info', {}).get('title', 'N/A')}")
        console.print(f"[cyan]Version:[/cyan] {data.get('info', {}).get('version', 'N/A')}")
        
        # Mostrar endpoints disponibles
        paths = data.get("paths", {})
        if paths:
            table = Table(title="Available Endpoints")
            table.add_column("Path", style="cyan")
            table.add_column("Methods", style="magenta")
            
            for path, methods in paths.items():
                method_list = ", ".join([m.upper() for m in methods.keys() if m != "parameters"])
                table.add_row(path, method_list)
            
            console.print(table)
    else:
        console.print(f"[red]✗[/red] OpenAPI failed: {response.status_code}")


def main():
    """Run all tests"""
    console.print(Panel.fit(
        "[bold yellow]Complexity Analyzer API Test Suite[/bold yellow]",
        border_style="cyan"
    ))
    
    try:
        test_root()
        test_docs()
        test_openapi()
        test_analyze()
        
        console.print("\n[bold green]All tests completed![/bold green]")
        
    except httpx.ConnectError:
        console.print("\n[bold red]Error: No se pudo conectar al servidor[/bold red]")
        console.print("Asegúrate de que el servidor esté corriendo:")
        console.print("  python scripts/run_dev.py")
    
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")


if __name__ == "__main__":
    main()