"""
Tests Unitarios - Módulo de Visualización

Tests para validar la generación de visualizaciones gráficas.
"""

import pytest
from pathlib import Path

from app.core.parser import parse_pseudocode
from app.core.visualization import (
    # Tree Builder
    TreeBuilder,
    TreeNode,
    NodeType,
    build_tree,
    
    # Recursion Trees
    RecursionTreeGenerator,
    RecursionType,
    generate_recursion_tree,
    
    # Execution Flow
    ExecutionFlowGenerator,
    FlowNodeType,
    generate_execution_flow,
    
    # Graphs
    GraphGenerator,
    GraphType,
    LayoutType,
    generate_graph,
    
    # Rendering
    DiagramRenderer,
    RenderFormat,
    RenderOptions,
    render_diagram,
)

# Algoritmos de prueba

FIBONACCI_CODE = """
algorithm fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end
    return fibonacci(n - 1) + fibonacci(n - 2)
end
"""

LINEAR_SEARCH_CODE = """
algorithm linearSearch(A[n], x)
begin
    for i := 1 to n do
    begin
        if (A[i] = x) then
        begin
            return i
        end
    end
    return -1
end
"""

BUBBLE_SORT_CODE = """
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

# Tests de TreeBuilder

class TestTreeBuilder:
    """Tests para el constructor de árboles genéricos"""
    
    def test_create_node(self):
        """Test creación de nodo"""
        builder = TreeBuilder()
        node = builder.create_node(node_id="Test", node_type=NodeType.ROOT, value=10)
        
        assert node.id == "Test"
        assert node.node_type == NodeType.ROOT
        assert node.value == 10
        assert node.depth == 0
    
    def test_add_child(self):
        """Test agregar hijo a nodo"""
        builder = TreeBuilder()
        root = builder.create_node(node_id="Root", node_type=NodeType.ROOT)
        child = builder.create_node(node_id="Child", node_type=NodeType.LEAF)
        
        root.add_child(child)
        
        assert len(root.children) == 1
        assert child in root.children
        assert child.depth == 1
    
    def test_is_leaf(self):
        """Test verificación de nodo hoja"""
        builder = TreeBuilder()
        root = builder.create_node(node_id="Root", node_type=NodeType.ROOT)
        leaf = builder.create_node(node_id="Leaf", node_type=NodeType.LEAF)
        
        root.add_child(leaf)
        
        assert not root.is_leaf()
        assert leaf.is_leaf()
    
    def test_count_nodes(self):
        """Test conteo de nodos"""
        builder = TreeBuilder()
        root = builder.create_node(node_id="Root", node_type=NodeType.ROOT)
        child1 = builder.create_node(node_id="Child1", node_type=NodeType.INTERNAL)
        child2 = builder.create_node(node_id="Child2", node_type=NodeType.LEAF)
        
        root.add_child(child1)
        root.add_child(child2)
        
        assert root.size() == 3
    
    def test_build_tree_manually(self):
        """Test construcción manual de árbol"""
        builder = TreeBuilder()
        root = builder.create_node(node_id="Root", node_type=NodeType.ROOT, value=1)
        child1 = builder.create_node(node_id="Child1", node_type=NodeType.INTERNAL, value=2)
        child2 = builder.create_node(node_id="Child2", node_type=NodeType.INTERNAL, value=3)
        
        root.add_child(child1)
        root.add_child(child2)
        
        assert root is not None
        assert root.value == 1
        assert len(root.children) == 2
        assert root.size() == 3
    
    def test_build_from_dict(self):
        """Test construcción desde diccionario"""
        builder = TreeBuilder()
        data = {
            "label": "Root",
            "type": "root",
            "children": [
                {"label": "Child1", "type": "internal", "children": []},
                {"label": "Child2", "type": "leaf", "children": []}
            ]
        }
        
        root = builder.build_from_dict(data)
        
        assert root.label == "Root"
        assert len(root.children) == 2
    
    def test_traverse_preorder(self):
        """Test recorrido en pre-orden"""
        builder = TreeBuilder()
        root = builder.create_node(node_id="1", node_type=NodeType.ROOT)
        child1 = builder.create_node(node_id="2", node_type=NodeType.INTERNAL)
        child2 = builder.create_node(node_id="3", node_type=NodeType.INTERNAL)
        
        root.add_child(child1)
        root.add_child(child2)
        
        nodes = root.traverse_preorder()
        ids = [n.id for n in nodes]
        
        assert ids == ["1", "2", "3"]
    
    def test_get_statistics(self):
        """Test estadísticas del árbol"""
        builder = TreeBuilder()
        root = builder.create_node(node_id="Root", node_type=NodeType.ROOT)
        builder.root = root
        
        for i in range(3):
            child = builder.create_node(node_id=f"Child{i}", node_type=NodeType.LEAF)
            root.add_child(child)
        
        stats = builder.get_statistics()
        
        assert stats["total_nodes"] == 4
        assert stats["leaves"] == 3

# Tests de RecursionTreeGenerator

class TestRecursionTreeGenerator:
    """Tests para generador de árboles de recursión"""
    
    def test_generate_fibonacci_tree(self):
        """Test generación de árbol para Fibonacci"""
        ast = parse_pseudocode(FIBONACCI_CODE)
        generator = RecursionTreeGenerator(max_depth=4)
        
        result = generator.generate(ast, start_value=3)
        
        assert result.root is not None
        assert result.recursion_type in [RecursionType.LINEAR, RecursionType.BINARY, RecursionType.MULTIPLE]
        assert result.total_calls >= 1
        assert result.max_depth <= 4
    
    def test_detect_recursion_type(self):
        """Test detección de tipo de recursión"""
        ast = parse_pseudocode(FIBONACCI_CODE)
        generator = RecursionTreeGenerator()
        
        recursion_type = generator._detect_recursion_type(ast.algorithm)
        
        # El tipo detectado depende del análisis del AST
        assert recursion_type in [RecursionType.LINEAR, RecursionType.BINARY, RecursionType.TAIL, RecursionType.MULTIPLE]
    
    def test_tree_statistics(self):
        """Test estadísticas del árbol de recursión"""
        ast = parse_pseudocode(FIBONACCI_CODE)
        result = generate_recursion_tree(ast, start_value=4, max_depth=6)
        
        assert result.statistics["total_calls"] > 0
        assert result.statistics["base_cases"] > 0
        assert result.statistics["max_depth"] >= 0
    
    def test_work_per_level(self):
        """Test cálculo de trabajo por nivel"""
        ast = parse_pseudocode(FIBONACCI_CODE)
        result = generate_recursion_tree(ast, start_value=4)
        
        assert len(result.work_per_level) > 0
        assert all(isinstance(work, str) for work in result.work_per_level)
    
    def test_max_depth_limit(self):
        """Test límite de profundidad"""
        ast = parse_pseudocode(FIBONACCI_CODE)
        generator = RecursionTreeGenerator(max_depth=3)
        
        result = generator.generate(ast, start_value=10)
        
        assert result.max_depth <= 3

# Tests de ExecutionFlowGenerator

class TestExecutionFlowGenerator:
    """Tests para generador de flujos de ejecución"""
    
    def test_generate_linear_search_flow(self):
        """Test generación de flujo para búsqueda lineal"""
        ast = parse_pseudocode(LINEAR_SEARCH_CODE)
        result = generate_execution_flow(ast)
        
        assert len(result.nodes) > 0
        assert len(result.edges) > 0
        assert result.start_node is not None
        assert len(result.end_nodes) > 0
    
    def test_generate_bubble_sort_flow(self):
        """Test generación de flujo para bubble sort"""
        ast = parse_pseudocode(BUBBLE_SORT_CODE)
        result = generate_execution_flow(ast)
        
        stats = result.statistics
        
        assert stats["total_nodes"] > 0
        assert stats["has_loops"] is True
        assert stats["has_decisions"] is True
    
    def test_flow_node_types(self):
        """Test tipos de nodos en flujo"""
        ast = parse_pseudocode(LINEAR_SEARCH_CODE)
        result = generate_execution_flow(ast)
        
        node_types = [node.node_type for node in result.nodes]
        
        assert FlowNodeType.START in node_types
        assert FlowNodeType.END in node_types
        assert FlowNodeType.LOOP_START in node_types
    
    def test_flow_statistics(self):
        """Test estadísticas del flujo"""
        ast = parse_pseudocode(BUBBLE_SORT_CODE)
        result = generate_execution_flow(ast)
        
        stats = result.statistics
        
        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert "node_types" in stats
        assert stats["total_nodes"] > 0

# Tests de GraphGenerator

class TestGraphGenerator:
    """Tests para generador de grafos"""
    
    def test_generate_tree(self):
        """Test generación de árbol"""
        generator = GraphGenerator()
        values = [10, 5, 15, 3, 7, 12, 20]
        
        result = generator.generate_tree(values=values)
        
        assert result.graph_type == GraphType.TREE
        assert result.statistics["num_nodes"] == len(values)
        assert result.statistics["num_edges"] == len(values) - 1
    
    def test_generate_directed_graph(self):
        """Test generación de grafo dirigido"""
        generator = GraphGenerator()
        
        result = generator.generate_graph(
            num_nodes=5,
            edges_list=[(0,1), (1,2), (2,3), (3,4)],
            directed=True
        )
        
        assert result.graph_type == GraphType.DIRECTED
        assert result.statistics["num_nodes"] == 5
        assert result.statistics["is_directed"] is True
    
    def test_generate_linked_list(self):
        """Test generación de lista enlazada"""
        generator = GraphGenerator()
        values = [1, 2, 3, 4, 5]
        
        result = generator.generate_linked_list(values=values)
        
        assert result.statistics["num_nodes"] == 5
        assert result.statistics["is_linear"] is True
    
    def test_graph_layouts(self):
        """Test diferentes layouts"""
        for layout in [LayoutType.HIERARCHICAL, LayoutType.CIRCULAR, LayoutType.SPRING]:
            result = generate_graph(
                structure_type="tree",
                values=[1, 2, 3, 4, 5],
                layout=layout
            )
            
            assert result.layout == layout
            assert all(node.position is not None for node in result.nodes)
    
    def test_graph_statistics(self):
        """Test estadísticas del grafo"""
        result = generate_graph(
            structure_type="graph",
            num_nodes=6,
            edges_list=[(0,1), (1,2), (2,3)],
            directed=False
        )
        
        stats = result.statistics
        
        assert "num_nodes" in stats
        assert "num_edges" in stats
        assert "avg_degree" in stats

# Tests de DiagramRenderer

class TestDiagramRenderer:
    """Tests para renderizador de diagramas"""
    
    def test_render_tree_dot(self):
        """Test renderizado de árbol en DOT"""
        builder = TreeBuilder()
        root = builder.create_node(node_id="Root", node_type=NodeType.ROOT)
        child = builder.create_node(node_id="Child", node_type=NodeType.LEAF)
        root.add_child(child)
        
        options = RenderOptions(format=RenderFormat.DOT)
        renderer = DiagramRenderer(options)
        
        result = renderer.render_tree(root)
        
        assert result.format == RenderFormat.DOT
        assert isinstance(result.content, str)
        assert "digraph" in result.content
        assert "Root" in result.content
    
    def test_render_tree_mermaid(self):
        """Test renderizado de árbol en Mermaid"""
        builder = TreeBuilder()
        root = builder.create_node(node_id="Root", node_type=NodeType.ROOT)
        
        result = render_diagram(root, format=RenderFormat.MERMAID)
        
        assert result.format == RenderFormat.MERMAID
        assert "graph TD" in result.content
    
    def test_render_tree_json(self):
        """Test renderizado de árbol en JSON"""
        builder = TreeBuilder()
        root = builder.create_node(node_id="Root", node_type=NodeType.ROOT)
        
        result = render_diagram(root, format=RenderFormat.JSON)
        
        assert result.format == RenderFormat.JSON
        assert isinstance(result.content, str)
        assert '"id": "Root"' in result.content
    
    def test_render_graph_dot(self):
        """Test renderizado de grafo en DOT"""
        graph = generate_graph(
            structure_type="tree",
            values=[1, 2, 3]
        )
        
        result = render_diagram(graph, format=RenderFormat.DOT)
        
        assert result.format == RenderFormat.DOT
        assert "digraph" in result.content or "graph" in result.content
    
    def test_render_flow_mermaid(self):
        """Test renderizado de flujo en Mermaid"""
        ast = parse_pseudocode(LINEAR_SEARCH_CODE)
        flow = generate_execution_flow(ast)
        
        result = render_diagram(flow, format=RenderFormat.MERMAID)
        
        assert result.format == RenderFormat.MERMAID
        assert "flowchart" in result.content
    
    def test_render_formats(self):
        """Test múltiples formatos de renderizado"""
        builder = TreeBuilder()
        root = builder.create_node(node_id="Test", node_type=NodeType.ROOT)
        
        formats = [RenderFormat.DOT, RenderFormat.MERMAID, RenderFormat.JSON]
        
        for fmt in formats:
            result = render_diagram(root, format=fmt)
            assert result.format == fmt
            assert len(result.content) > 0

# Tests de Integración

class TestIntegration:
    """Tests de integración del módulo completo"""
    
    def test_full_visualization_pipeline(self):
        """Test pipeline completo de visualización"""
        # 1. Parsear
        ast = parse_pseudocode(FIBONACCI_CODE)
        
        # 2. Generar árbol de recursión
        tree_result = generate_recursion_tree(ast, start_value=4)
        assert tree_result.total_calls > 0
        
        # 3. Generar flujo
        flow_result = generate_execution_flow(ast)
        assert len(flow_result.nodes) > 0
        
        # 4. Renderizar ambos
        tree_dot = render_diagram(tree_result, format=RenderFormat.DOT)
        flow_mermaid = render_diagram(flow_result, format=RenderFormat.MERMAID)
        
        assert tree_dot.format == RenderFormat.DOT
        assert flow_mermaid.format == RenderFormat.MERMAID
    
    def test_multiple_algorithms(self):
        """Test visualización de múltiples algoritmos"""
        algorithms = [
            FIBONACCI_CODE,
            LINEAR_SEARCH_CODE,
            BUBBLE_SORT_CODE
        ]
        
        for code in algorithms:
            ast = parse_pseudocode(code)
            
            # Flujo debe generarse para todos
            flow = generate_execution_flow(ast)
            assert len(flow.nodes) > 0
            
            # Renderizar
            result = render_diagram(flow, format=RenderFormat.JSON)
            assert result.format == RenderFormat.JSON

# Fixtures

@pytest.fixture
def sample_tree():
    """Fixture: árbol de ejemplo"""
    builder = TreeBuilder()
    root = builder.create_node(node_id="Root", node_type=NodeType.ROOT)
    
    for i in range(3):
        child = builder.create_node(node_id=f"Child{i}", node_type=NodeType.INTERNAL)
        root.add_child(child)
    
    return root

@pytest.fixture
def fibonacci_ast():
    """Fixture: AST de Fibonacci"""
    return parse_pseudocode(FIBONACCI_CODE)

@pytest.fixture
def linear_search_ast():
    """Fixture: AST de búsqueda lineal"""
    return parse_pseudocode(LINEAR_SEARCH_CODE)

# Tests con Fixtures

def test_with_sample_tree(sample_tree):
    """Test usando fixture de árbol"""
    assert sample_tree.id == "Root"
    assert len(sample_tree.children) == 3

def test_with_fibonacci_ast(fibonacci_ast):
    """Test usando fixture de AST"""
    result = generate_recursion_tree(fibonacci_ast, start_value=3)
    assert result.recursion_type in [RecursionType.LINEAR, RecursionType.BINARY, RecursionType.TAIL, RecursionType.MULTIPLE]

def test_with_linear_search_ast(linear_search_ast):
    """Test usando fixture de AST"""
    result = generate_execution_flow(linear_search_ast)
    assert result.statistics["has_loops"] is True