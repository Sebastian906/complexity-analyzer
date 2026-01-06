"""
Script de Demostración - Módulo de Visualización

Script para probar el módulo de visualización con diferentes algoritmos.
Ejecutar: python scripts/demo_visualization.py
"""

import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.parser import parse_pseudocode
from app.core.visualization import (
    generate_recursion_tree,
    generate_execution_flow,
    generate_graph,
    render_diagram,
    RenderFormat
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def demo_recursion_tree():
    """Demo: Árbol de recursión"""
    print("DEMO 1: ÁRBOL DE RECURSIÓN - Fibonacci")
    
    code = """
algorithm fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end
    return fibonacci(n - 1) + fibonacci(n - 2)
end
"""
    
    print("\nCódigo:")
    print(code)
    
    try:
        # Parsear
        ast = parse_pseudocode(code)
        
        # Generar árbol de recursión
        print("\nGenerando árbol de recursión...")
        result = generate_recursion_tree(ast, start_value=4, max_depth=5)
        
        print(f"\n✓ Árbol generado exitosamente")
        print(f"  Tipo de recursión: {result.recursion_type.value}")
        print(f"  Total de llamadas: {result.total_calls}")
        print(f"  Profundidad máxima: {result.max_depth}")
        print(f"  Casos base: {result.base_cases}")
        print(f"  Trabajo total: {result.total_work}")
        
        print(f"\n  Trabajo por nivel:")
        for i, work in enumerate(result.work_per_level):
            print(f"    Nivel {i}: {work}")
        
        # Renderizar en diferentes formatos
        print("\nRenderizando en diferentes formatos...")
        
        # DOT
        dot_result = render_diagram(result, format=RenderFormat.DOT)
        print(f"\n✓ Renderizado en DOT:")
        print(dot_result.content[:200] + "...")
        
        # Mermaid
        mermaid_result = render_diagram(result, format=RenderFormat.MERMAID)
        print(f"\n✓ Renderizado en Mermaid:")
        print(mermaid_result.content[:200] + "...")
        
        # JSON
        json_result = render_diagram(result, format=RenderFormat.JSON)
        print(f"\n✓ Renderizado en JSON")
        
        # Guardar en archivo (comentado para evitar crear archivos)
        # output_path = Path("data/exports/images/fibonacci_tree.svg")
        # svg_result = render_diagram(result, format=RenderFormat.SVG, output_path=output_path)
        # print(f"\n✓ Guardado en: {svg_result.file_path}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        logger.exception("Error en demo_recursion_tree")


def demo_execution_flow():
    """Demo: Flujo de ejecución"""
    print("DEMO 2: FLUJO DE EJECUCIÓN - Bubble Sort")
    
    code = """
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
"""
    
    print("\nCódigo:")
    print(code)
    
    try:
        # Parsear
        ast = parse_pseudocode(code)
        
        # Generar flujo
        print("\nGenerando flujo de ejecución...")
        result = generate_execution_flow(ast)
        
        print(f"\n✓ Flujo generado exitosamente")
        print(f"  Total de nodos: {result.statistics['total_nodes']}")
        print(f"  Total de aristas: {result.statistics['total_edges']}")
        print(f"  Tiene loops: {result.statistics['has_loops']}")
        print(f"  Tiene decisiones: {result.statistics['has_decisions']}")
        
        print(f"\n  Tipos de nodos:")
        for node_type, count in result.statistics['node_types'].items():
            print(f"    {node_type}: {count}")
        
        # Renderizar
        print("\nRenderizando flujo...")
        
        # Mermaid flowchart
        mermaid_result = render_diagram(result, format=RenderFormat.MERMAID)
        print(f"\n✓ Renderizado en Mermaid:")
        print(mermaid_result.content[:300] + "...")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        logger.exception("Error en demo_execution_flow")


def demo_graph_generation():
    """Demo: Generación de grafos"""
    print("DEMO 3: GENERACIÓN DE GRAFOS")
    
    try:
        # Árbol binario
        print("\n--- Árbol Binario ---")
        tree_result = generate_graph(
            structure_type="tree",
            values=[10, 5, 15, 3, 7, 12, 20]
        )
        
        print(f"✓ Árbol generado")
        print(f"  Nodos: {tree_result.statistics['num_nodes']}")
        print(f"  Aristas: {tree_result.statistics['num_edges']}")
        print(f"  Tipo: {tree_result.graph_type.value}")
        
        # Renderizar en DOT
        dot_result = render_diagram(tree_result, format=RenderFormat.DOT)
        print(f"\n  Renderizado DOT:")
        print(dot_result.content[:200] + "...")
        
        # Grafo dirigido
        print("\n--- Grafo Dirigido ---")
        graph_result = generate_graph(
            structure_type="graph",
            num_nodes=6,
            edges_list=[(0,1), (0,2), (1,3), (1,4), (2,4), (3,5), (4,5)],
            directed=True
        )
        
        print(f"✓ Grafo generado")
        print(f"  Nodos: {graph_result.statistics['num_nodes']}")
        print(f"  Aristas: {graph_result.statistics['num_edges']}")
        print(f"  Conexo (débilmente): {graph_result.statistics.get('is_weakly_connected', 'N/A')}")
        
        # Lista enlazada
        print("\n--- Lista Enlazada ---")
        list_result = generate_graph(
            structure_type="linked_list",
            values=[1, 2, 3, 4, 5]
        )
        
        print(f"✓ Lista generada")
        print(f"  Nodos: {list_result.statistics['num_nodes']}")
        print(f"  Es lineal: {list_result.statistics.get('is_linear', False)}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        logger.exception("Error en demo_graph_generation")


def demo_comprehensive():
    """Demo: Análisis completo con visualización"""
    print("DEMO 4: ANÁLISIS COMPLETO - Merge Sort")
    
    code = """
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
"""
    
    print("\nCódigo:")
    print(code)
    
    try:
        # Parsear
        ast = parse_pseudocode(code)
        
        print("\n1. Generando árbol de recursión...")
        tree_result = generate_recursion_tree(ast, start_value=8, max_depth=4)
        print(f"   ✓ {tree_result.total_calls} llamadas, prof. {tree_result.max_depth}")
        
        print("\n2. Generando flujo de ejecución...")
        flow_result = generate_execution_flow(ast)
        print(f"   ✓ {flow_result.statistics['total_nodes']} nodos de flujo")
        
        print("\n3. Renderizando visualizaciones...")
        
        # Árbol en Mermaid
        tree_mermaid = render_diagram(tree_result, format=RenderFormat.MERMAID)
        print(f"   ✓ Árbol de recursión (Mermaid): {len(tree_mermaid.content)} chars")
        
        # Flujo en DOT
        flow_dot = render_diagram(flow_result, format=RenderFormat.DOT)
        print(f"   ✓ Flujo de ejecución (DOT): {len(flow_dot.content)} chars")
        
        print("\n✓ Análisis completo exitoso")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        logger.exception("Error en demo_comprehensive")


def main():
    """Función principal"""
    print("DEMOSTRACIÓN - MÓDULO DE VISUALIZACIÓN")
    
    try:
        # Demo 1: Árbol de recursión
        demo_recursion_tree()
        
        input("\n[Presiona Enter para continuar...]")
        
        # Demo 2: Flujo de ejecución
        demo_execution_flow()
        
        input("\n[Presiona Enter para continuar...]")
        
        # Demo 3: Generación de grafos
        demo_graph_generation()
        
        input("\n[Presiona Enter para continuar...]")
        
        # Demo 4: Análisis completo
        demo_comprehensive()
        
        print("✓ TODAS LAS DEMOS COMPLETADAS EXITOSAMENTE")
        
    except KeyboardInterrupt:
        print("\n\n✗ Interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n✗ Error inesperado: {e}")
        logger.exception("Error en main")


if __name__ == "__main__":
    main()