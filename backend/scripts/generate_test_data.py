"""
Script para generar datos de prueba sintéticos

Genera algoritmos de ejemplo en múltiples categorías para testing y validación.
Útil para:
- Poblar base de datos de desarrollo
- Testing de endpoints
- Validación de detectores de patrones
- Benchmarking de performance

Uso:
    python scripts/generate_test_data.py --count 50 --output data/algorithms/test_data/ 
    python scripts/generate_test_data.py --category sorting --count 10
"""

import sys
from pathlib import Path
from typing import List, Dict
import json
import random

# Agregar raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.core.config import settings

class TestDataGenerator:
    """Generador de algoritmos de prueba sintéticos"""

    # Templates de algoritmos por categoría
    TEMPLATES = {
        "sorting": [
            {
                "name": "bubbleSort",
                "code": """algorithm bubbleSort(A[1..n])
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
end""",
                "expected_complexity": "O(n²)",
                "pattern": "brute_force",
                "tags": ["sorting", "quadratic", "in-place"]
            },
            {
                "name": "quickSort",
                "code": """algorithm quickSort(A[1..n], low, high)
begin
    if (low < high) then
    begin
        pivot ← partition(A, low, high)
        call quickSort(A, low, pivot - 1)
        call quickSort(A, pivot + 1, high)
    end
end""",
                "expected_complexity": "O(n log n)",
                "pattern": "divide_and_conquer",
                "tags": ["sorting", "divide-conquer", "recursive"]
            },
            {
                "name": "mergeSort",
                "code": """algorithm mergeSort(A[1..n])
begin
    if (n > 1) then
    begin
        mid ← n / 2
        call mergeSort(A[1..mid])
        call mergeSort(A[mid+1..n])
        call merge(A, 1, mid, n)
    end
end""",
                "expected_complexity": "O(n log n)",
                "pattern": "divide_and_conquer",
                "tags": ["sorting", "divide-conquer", "stable"]
            },
            {
                "name": "insertionSort",
                "code": """algorithm insertionSort(A[1..n])
begin
    for i ← 2 to n do
    begin
        key ← A[i]
        j ← i - 1
        while (j > 0 and A[j] > key) do
        begin
            A[j + 1] ← A[j]
            j ← j - 1
        end
        A[j + 1] ← key
    end
end""",
                "expected_complexity": "O(n²)",
                "pattern": "brute_force",
                "tags": ["sorting", "adaptive", "in-place"]
            },
        ],

        "searching": [
            {
                "name": "linearSearch",
                "code": """algorithm linearSearch(A[1..n], x)
begin
    for i ← 1 to n do
    begin
        if (A[i] = x) then
        begin
            return i
        end
    end
    return -1
end""",
                "expected_complexity": "O(n)",
                "pattern": "brute_force",
                "tags": ["searching", "linear"]
            },
            {
                "name": "binarySearch",
                "code": """algorithm binarySearch(A[1..n], x)
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
end""",
                "expected_complexity": "O(log n)",
                "pattern": "divide_and_conquer",
                "tags": ["searching", "binary", "logarithmic"]
            },
        ],
        
        "recursion": [
            {
                "name": "factorial",
                "code": """algorithm factorial(n)
begin
    if (n <= 1) then
    begin
        return 1
    end
    return n * factorial(n - 1)
end""",
                "expected_complexity": "O(n)",
                "pattern": "recursion",
                "tags": ["recursion", "mathematical"]
            },
            {
                "name": "fibonacci",
                "code": """algorithm fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end
    return fibonacci(n - 1) + fibonacci(n - 2)
end""",
                "expected_complexity": "O(2^n)",
                "pattern": "recursion",
                "tags": ["recursion", "exponential"]
            },
            {
                "name": "fibonacciDP",
                "code": """algorithm fibonacciDP(n)
begin
    dp[0] ← 0
    dp[1] ← 1

    for i ← 2 to n do
    begin
        dp[i] ← dp[i-1] + dp[i-2]
    end
    
    return dp[n]
end""",
                "expected_complexity": "O(n)",
                "pattern": "dynamic_programming",
                "tags": ["dynamic-programming", "memoization"]
            },
        ],
        
        "graphs": [
            {
                "name": "DFS",
                "code": """algorithm DFS(G, v)
begin
    visited[v] ← true
    
    for each u in G.adjacent(v) do
    begin
        if (not visited[u]) then
        begin
            call DFS(G, u)
        end
    end
end""",
                "expected_complexity": "O(V + E)",
                "pattern": "recursion",
                "tags": ["graphs", "dfs", "traversal"]
            },
            {
                "name": "BFS",
                "code": """algorithm BFS(G, s)
begin
    Q ← empty queue
    visited[s] ← true
    Q.enqueue(s)
    
    while (not Q.isEmpty()) do
    begin
        v ← Q.dequeue()
        
        for each u in G.adjacent(v) do
        begin
            if (not visited[u]) then
            begin
                visited[u] ← true
                Q.enqueue(u)
            end
        end
    end
end""",
                "expected_complexity": "O(V + E)",
                "pattern": "brute_force",
                "tags": ["graphs", "bfs", "traversal"]
            },
        ],

        "dynamic_programming": [
            {
                "name": "knapsack",
                "code": """algorithm knapsack(W, weights[1..n], values[1..n])
begin
    for i ← 0 to n do
    begin
        for w ← 0 to W do
        begin
            if (i = 0 or w = 0) then
            begin
                dp[i][w] ← 0
            end
            else
            begin
                if (weights[i-1] <= w) then
                begin
                    dp[i][w] ← max(values[i-1] + dp[i-1][w-weights[i-1]], dp[i-1][w])
                end
                else
                begin
                    dp[i][w] ← dp[i-1][w]
                end
            end
        end
    end
    return dp[n][W]
end""",
                "expected_complexity": "O(nW)",
                "pattern": "dynamic_programming",
                "tags": ["dynamic-programming", "optimization"]
            },
        ],

        "greedy": [
            {
                "name": "dijkstra",
                "code": """algorithm dijkstra(G, source)
begin
    for each vertex v in G do
    begin
        dist[v] ← infinity
        visited[v] ← false
    end
    
    dist[source] ← 0
    
    for i ← 1 to n do
    begin
        u ← vertex with minimum dist and not visited
        visited[u] ← true
        
        for each neighbor v of u do
        begin
            if (dist[u] + weight(u,v) < dist[v]) then
            begin
                dist[v] ← dist[u] + weight(u,v)
            end
        end
    end
end""",
                "expected_complexity": "O(V²)",
                "pattern": "greedy",
                "tags": ["greedy", "graphs", "shortest-path"]
            },
        ],
    }

    def __init__(self, output_dir: Path = None):
        """
        Inicializa el generador

        Args:
            output_dir: Directorio de salida (default: data/algorithms/)
        """
        self.output_dir = output_dir or settings.ALGORITHMS_PATH
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_by_category(
        self,
        category: str,
        count: int = None
    ) -> List[Dict]:
        """
        Genera algoritmos de una categoría específica

        Args:
            category: Categoría (sorting, searching, etc.)
            count: Número de algoritmos (None = todos)

        Returns:
            Lista de algoritmos generados
        """
        if category not in self.TEMPLATES:
            raise ValueError(f"Categoría '{category}' no válida. Opciones: {list(self.TEMPLATES.keys())}")

        templates = self.TEMPLATES[category]

        if count is not None:
            # Repetir templates si count > len(templates)
            templates = (templates * ((count // len(templates)) + 1))[:count]

        algorithms = []

        for i, template in enumerate(templates):
            algo = {
                "name": f"{template['name']}_{i+1}" if count and count > len(self.TEMPLATES[category]) else template['name'],
                "code": template['code'],
                "category": category,
                "expected_big_o": template['expected_complexity'],
                "expected_pattern": template['pattern'],
                "tags": template['tags'],
                "metadata": {
                    "generated": True,
                    "template": template['name']
                }
            }

            algorithms.append(algo)

        return algorithms

    def generate_all(self, count_per_category: int = None) -> Dict[str, List[Dict]]:
        """
        Genera algoritmos de todas las categorías

        Args:
            count_per_category: Algoritmos por categoría (None = todos los templates)

        Returns:
            Diccionario {categoria: [algoritmos]}
        """
        all_algorithms = {}

        for category in self.TEMPLATES.keys():
            algorithms = self.generate_by_category(category, count_per_category)
            all_algorithms[category] = algorithms

        return all_algorithms

    def save_to_files(self, algorithms: List[Dict], prefix: str = "generated"):
        """
        Guarda algoritmos en archivos .txt

        Args:
            algorithms: Lista de algoritmos
            prefix: Prefijo para nombres de archivo
        """
        for i, algo in enumerate(algorithms):
            filename = f"{prefix}_{algo['name']}.txt"
            filepath = self.output_dir / filename

            filepath.write_text(algo['code'], encoding='utf-8')

            # Guardar metadata en JSON
            metadata_file = filepath.with_suffix('.json')
            metadata = {
                "name": algo['name'],
                "category": algo['category'],
                "expected_big_o": algo['expected_big_o'],
                "expected_pattern": algo['expected_pattern'],
                "tags": algo['tags'],
                "metadata": algo.get('metadata', {})
            }

            metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

        print(f"✓ Guardados {len(algorithms)} algoritmos en {self.output_dir}")

    def save_to_json(self, algorithms: Dict[str, List[Dict]], filename: str = "test_algorithms.json"):
        """
        Guarda todos los algoritmos en un JSON
        
        Args:
            algorithms: Diccionario de algoritmos por categoría
            filename: Nombre del archivo JSON
        """
        filepath = self.output_dir / filename

        filepath.write_text(json.dumps(algorithms, indent=2), encoding='utf-8')

        total = sum(len(algos) for algos in algorithms.values())
        print(f"✓ Guardados {total} algoritmos en {filepath}")

def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description="Generador de datos de prueba")
    parser.add_argument(
        "--category",
        choices=list(TestDataGenerator.TEMPLATES.keys()) + ["all"],
        default="all",
        help="Categoría de algoritmos"
    )
    parser.add_argument(
        "--count",
        type=int,
        help="Número de algoritmos por categoría"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Directorio de salida"
    )
    parser.add_argument(
        "--format",
        choices=["files", "json", "both"],
        default="both",
        help="Formato de salida"
    )

    args = parser.parse_args()

    # Crear generador
    generator = TestDataGenerator(output_dir=args.output)

    print(f"Generando datos de prueba...")
    print(f"Categoría: {args.category}")
    print(f"Count: {args.count or 'all templates'}")
    print(f"Output: {generator.output_dir}")
    print()

    # Generar
    if args.category == "all":
        algorithms = generator.generate_all(count_per_category=args.count)

        if args.format in ["files", "both"]:
            for category, algos in algorithms.items():
                generator.save_to_files(algos, prefix=category)

        if args.format in ["json", "both"]:
            generator.save_to_json(algorithms)
    else:
        algorithms = generator.generate_by_category(args.category, args.count)

        if args.format in ["files", "both"]:
            generator.save_to_files(algorithms, prefix=args.category)

        if args.format in ["json", "both"]:
            generator.save_to_json({args.category: algorithms})

    print()
    print("Generación completada")

if __name__ == "__main__":
    main()