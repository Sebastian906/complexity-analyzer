"""
Script de Test - Validación de Correcciones en Detección de Patrones

Prueba que los detectores corregidos identifiquen correctamente:
1. QuickSort como Divide y Conquista (NO backtracking)
2. N-Queens como Backtracking (NO divide y conquista)
3. Fibonacci simple como Recursión (NO backtracking/D&C)
4. Bubble Sort como Fuerza Bruta (NO greedy)

Uso:
    python scripts/test_pattern_detection_fixes.py
"""

import importlib
import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from app.core.parser.pseudocode_parser import PseudocodeParser
from app.core.patterns.pattern_detector import PatternDetector

# Forzar recarga de módulos
if 'app.core.patterns.detectors.recursive_detector' in sys.modules:
    importlib.reload(sys.modules['app.core.patterns.detectors.recursive_detector'])
if 'app.core.patterns.detectors.brute_force_detector' in sys.modules:
    importlib.reload(sys.modules['app.core.patterns.detectors.brute_force_detector'])

console = Console()

# CASOS DE PRUEBA - CORREGIDOS
TEST_CASES = {
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
        "expected_primary": "Divide y Vencerás",
        "should_not_be": ["Backtracking", "Branch and Bound", "Greedy"],
        "description": "QuickSort - D&C clásico"
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
        "expected_primary": "Divide y Vencerás",
        "should_not_be": ["Backtracking", "Fuerza Bruta"],
        "description": "MergeSort - D&C con merge"
    },
    
    "binary_search": {
    "code": """algorithm binary_search(A[1..n], x)
begin
    low ← 1
    high ← n
    while (low <= high) do
    begin
        mid ← (low + high) / 2
        if A[mid] = x then
        begin
            return mid
        end
        else
        begin
            if A[mid] < x then
            begin
                low ← mid + 1
            end
            else
            begin
                high ← mid - 1
            end
        end
    end
    return -1
end""",
        "expected_primary": "Divide y Vencerás",
        "should_not_be": ["Backtracking", "Fuerza Bruta", "Greedy"],
        "description": "Binary Search - D&C iterativo"
    },
    
    "n_queens": {
        "code": """algorithm n_queens(board[1..n][1..n], row)
begin
    if row > n then
    begin
        return true
    end
    
    for col ← 1 to n do
    begin
        if is_safe(board, row, col) then
        begin
            board[row][col] ← 1
            call n_queens(board, row + 1)
            board[row][col] ← 0
        end
    end
    return false
end""",
        "expected_primary": "Backtracking",
        "should_not_be": ["Divide y Vencerás", "Programación Dinámica"],
        "description": "N-Queens - Backtracking clásico"
    },
    
    "fibonacci_simple": {
        "code": """algorithm fibonacci(n)
begin
    if n <= 1 then
    begin
        return n
    end
    else
    begin
        return fibonacci(n - 1) + fibonacci(n - 2)
    end
end""",
        "expected_primary": "Recursión",
        "should_not_be": ["Backtracking", "Divide y Conquista", "Programación Dinámica"],
        "description": "Fibonacci recursivo simple"
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
        "expected_primary": "Fuerza Bruta",
        "should_not_be": ["Greedy", "Divide y Conquista", "Backtracking"],
        "description": "Bubble Sort - Fuerza bruta con swaps"
    },
    
    "fibonacci_dp": {
        "code": """algorithm fibonacci_dp(n)
begin
    dp[0] ← 0
    dp[1] ← 1
    for i ← 2 to n do
    begin
        dp[i] ← dp[i-1] + dp[i-2]
    end
    return dp[n]
end""",
        "expected_primary": "Programación Dinámica",
        "should_not_be": ["Fuerza Bruta", "Backtracking"],
        "description": "Fibonacci DP - bottom-up"
    },
}

def test_algorithm(name: str, test_case: dict) -> dict:
    """Prueba un algoritmo y retorna resultados"""
    console.print(f"\n[cyan]Testing:[/cyan] [yellow]{name}[/yellow]")
    console.print(f"[dim]{test_case['description']}[/dim]")
    
    try:
        # Parsear
        parser = PseudocodeParser()
        ast = parser.parse(test_case["code"])
        
        # Detectar patrones
        detector = PatternDetector()
        result = detector.detect(ast, min_confidence=0.0)
        
        # Obtener patrón primario
        primary = result.primary_pattern_name if result.primary_pattern else "None"
        primary_confidence = result.primary_confidence if result.primary_pattern else 0.0
        
        # Top 3
        confident = [
            (p.pattern.pattern_name, p.final_score)
            for p in result.confident_patterns
            if p.final_score >= 0.20
        ]
        
        console.print("[dim]Top 3 patrones detectados:[/dim]")
        for pattern_name, score in confident[:3]:
            console.print(f"  [dim]- {pattern_name}: {score*100:.1f}%[/dim]")
        
        # Verificar expectativas
        success = primary == test_case["expected_primary"]
        
        # Verificar que NO aparezcan patrones incorrectos
        false_positives = []
        for pattern_name, score in confident:
            if pattern_name in test_case["should_not_be"] and score >= 0.5:
                false_positives.append((pattern_name, score))
        
        return {
            "name": name,
            "success": success and len(false_positives) == 0,
            "primary_detected": primary,
            "primary_confidence": primary_confidence,
            "expected": test_case["expected_primary"],
            "all_confident": confident,
            "false_positives": false_positives,
        }
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "name": name,
            "success": False,
            "error": str(e),
        }

def print_results(results: list):
    """Imprime tabla de resultados"""
    console.print("\n" + "="*80)
    console.print("[bold cyan]RESULTADOS DE PRUEBAS[/bold cyan]\n")
    
    table = Table(show_header=True)
    table.add_column("Test", style="cyan", width=20)
    table.add_column("Esperado", style="white", width=20)
    table.add_column("Detectado", style="yellow", width=20)
    table.add_column("Confianza", style="green", justify="right", width=10)
    table.add_column("Estado", style="bold", justify="center", width=8)
    
    passed = 0
    failed = 0
    
    for result in results:
        if "error" in result:
            table.add_row(
                result["name"],
                "N/A",
                "ERROR",
                "N/A",
                "[red]✗[/red]"
            )
            failed += 1
            continue
        
        status = "[green]✓[/green]" if result["success"] else "[red]✗[/red]"
        
        table.add_row(
            result["name"],
            result["expected"],
            result["primary_detected"],
            f"{result['primary_confidence']*100:.1f}%",
            status
        )
        
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    console.print(table)
    
    # Detalles de falsos positivos
    console.print("\n[bold yellow]FALSOS POSITIVOS DETECTADOS:[/bold yellow]")
    has_fps = False
    for result in results:
        if "false_positives" in result and result["false_positives"]:
            has_fps = True
            console.print(f"\n[red]{result['name']}:[/red]")
            for pattern, score in result["false_positives"]:
                console.print(f"  - {pattern}: {score*100:.1f}% (NO debería estar)")
    
    if not has_fps:
        console.print("  [green]Ninguno - ¡Excelente![/green]")
    
    # Análisis de fallos
    console.print("\n[bold yellow]ANÁLISIS DE FALLOS:[/bold yellow]")
    for result in results:
        if not result.get("success", False) and "error" not in result:
            console.print(f"\n[red]{result['name']}:[/red]")
            console.print(f"  Esperado: [cyan]{result['expected']}[/cyan]")
            console.print(f"  Obtenido: [yellow]{result['primary_detected']}[/yellow] ({result['primary_confidence']*100:.1f}%)")
            
            if result.get("all_confident"):
                console.print("  [dim]Otros patrones detectados:[/dim]")
                for name, score in result["all_confident"][:5]:
                    console.print(f"    - {name}: {score*100:.1f}%")
    
    # Resumen
    total = len(results)
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        f"[bold]RESUMEN[/bold]\n\n"
        f"[green]Pasados:[/green] {passed}/{total}\n"
        f"[red]Fallidos:[/red] {failed}/{total}\n"
        f"[cyan]Tasa de éxito:[/cyan] {passed/total*100:.1f}%",
        border_style="green" if failed == 0 else "red"
    ))

def main():
    """Ejecuta todos los tests"""
    console.print(Panel.fit(
        "[bold yellow]Test de Correcciones - Detección de Patrones[/bold yellow]\n"
        "[dim]Validando que los detectores identifiquen correctamente cada patrón[/dim]",
        border_style="cyan"
    ))
    
    results = []
    
    for name, test_case in TEST_CASES.items():
        result = test_algorithm(name, test_case)
        results.append(result)
    
    print_results(results)
    
    # Return code
    all_passed = all(r.get("success", False) for r in results)
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrumpidos[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)