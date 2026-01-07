"""
Optimizer para Visualizaciones
Optimiza la generación y renderizado de grafos grandes
"""
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import math
from collections import defaultdict

from app.utils.logger import get_logger

logger = get_logger(__name__)

class OptimizationLevel(str, Enum):
    """Niveles de optimización"""
    NONE = "none"
    BASIC = "basic"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

@dataclass
class OptimizationConfig:
    """Configuración de optimización"""
    level: OptimizationLevel = OptimizationLevel.MODERATE
    max_nodes: int = 1000
    max_edges: int = 5000
    enable_clustering: bool = True
    enable_simplification: bool = True
    enable_level_of_detail: bool = True
    edge_bundling: bool = True
    node_aggregation: bool = True
    prune_redundant: bool = True

@dataclass
class GraphMetrics:
    """Métricas de un grafo"""
    num_nodes: int
    num_edges: int
    max_degree: int
    avg_degree: float
    density: float
    is_sparse: bool
    estimated_complexity: str

class VisualizationOptimizer:
    """
    Optimizador de visualizaciones para manejar grafos grandes
    de forma eficiente
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self._cache = {}
    
    def optimize_graph(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Tuple[str, str, Dict[str, Any]]],
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict], List[Tuple], Dict[str, Any]]:
        """
        Optimiza un grafo para visualización
        
        Args:
            nodes: Lista de nodos
            edges: Lista de aristas (source, target, attrs)
            options: Opciones adicionales
            
        Returns:
            (nodos_optimizados, aristas_optimizadas, metadata)
        """
        logger.info(f"Optimizando grafo: {len(nodes)} nodos, {len(edges)} aristas")
        
        # Calcular métricas
        metrics = self._calculate_metrics(nodes, edges)
        
        # Determinar estrategia de optimización
        if self.config.level == OptimizationLevel.NONE:
            return nodes, edges, {'metrics': metrics, 'optimizations': []}
        
        optimizations_applied = []
        optimized_nodes = nodes.copy()
        optimized_edges = edges.copy()
        
        # Optimización básica: remover duplicados y nodos aislados
        if metrics.num_nodes > self.config.max_nodes // 2:
            optimized_nodes, optimized_edges = self._remove_duplicates(
                optimized_nodes, optimized_edges
            )
            optimizations_applied.append('remove_duplicates')
        
        # Poda de nodos redundantes
        if self.config.prune_redundant and metrics.num_nodes > 100:
            optimized_nodes, optimized_edges = self._prune_redundant_nodes(
                optimized_nodes, optimized_edges
            )
            optimizations_applied.append('prune_redundant')
        
        # Agregación de nodos (para grafos muy grandes)
        if (self.config.node_aggregation and 
            metrics.num_nodes > self.config.max_nodes):
            optimized_nodes, optimized_edges = self._aggregate_nodes(
                optimized_nodes, optimized_edges
            )
            optimizations_applied.append('node_aggregation')
        
        # Clustering jerárquico
        if (self.config.enable_clustering and 
            metrics.num_nodes > self.config.max_nodes // 2):
            optimized_nodes, optimized_edges, cluster_info = self._apply_clustering(
                optimized_nodes, optimized_edges
            )
            optimizations_applied.append('clustering')
        
        # Simplificación de aristas
        if (self.config.enable_simplification and 
            metrics.num_edges > self.config.max_edges):
            optimized_edges = self._simplify_edges(
                optimized_nodes, optimized_edges
            )
            optimizations_applied.append('edge_simplification')
        
        # Edge bundling (para mejorar legibilidad)
        if self.config.edge_bundling and metrics.density > 0.3:
            optimized_edges = self._bundle_edges(
                optimized_nodes, optimized_edges
            )
            optimizations_applied.append('edge_bundling')
        
        # Level of Detail (LOD)
        if self.config.enable_level_of_detail:
            optimized_nodes = self._apply_lod(optimized_nodes, metrics)
            optimizations_applied.append('level_of_detail')
        
        logger.info(
            f"Optimización completada: {len(optimized_nodes)} nodos, "
            f"{len(optimized_edges)} aristas. "
            f"Aplicadas: {', '.join(optimizations_applied)}"
        )
        
        metadata = {
            'original_metrics': metrics,
            'optimized_metrics': self._calculate_metrics(
                optimized_nodes, optimized_edges
            ),
            'optimizations_applied': optimizations_applied,
            'reduction_ratio': {
                'nodes': 1 - len(optimized_nodes) / max(len(nodes), 1),
                'edges': 1 - len(optimized_edges) / max(len(edges), 1)
            }
        }
        
        return optimized_nodes, optimized_edges, metadata
    
    def _calculate_metrics(
        self,
        nodes: List[Dict],
        edges: List[Tuple]
    ) -> GraphMetrics:
        """Calcula métricas del grafo"""
        n = len(nodes)
        m = len(edges)
        
        if n == 0:
            return GraphMetrics(0, 0, 0, 0.0, 0.0, True, "O(1)")
        
        # Calcular grados
        degree_map = defaultdict(int)
        for source, target, _ in edges:
            degree_map[source] += 1
            degree_map[target] += 1
        
        max_degree = max(degree_map.values()) if degree_map else 0
        avg_degree = sum(degree_map.values()) / n if n > 0 else 0
        
        # Densidad: m / (n * (n-1) / 2)
        max_edges = n * (n - 1) / 2
        density = m / max_edges if max_edges > 0 else 0
        
        # Es disperso si density < 0.1
        is_sparse = density < 0.1
        
        # Estimar complejidad de renderizado
        complexity = self._estimate_rendering_complexity(n, m, density)
        
        return GraphMetrics(
            num_nodes=n,
            num_edges=m,
            max_degree=max_degree,
            avg_degree=avg_degree,
            density=density,
            is_sparse=is_sparse,
            estimated_complexity=complexity
        )
    
    def _estimate_rendering_complexity(
        self,
        n: int,
        m: int,
        density: float
    ) -> str:
        """Estima la complejidad de renderizado"""
        if n <= 10:
            return "O(1)"
        elif n <= 100:
            return "O(n log n)"
        elif n <= 1000:
            if density < 0.1:
                return "O(n + m)"
            else:
                return "O(n²)"
        else:
            if density < 0.05:
                return "O(n + m)"
            else:
                return "O(n² log n)"
    
    def _remove_duplicates(
        self,
        nodes: List[Dict],
        edges: List[Tuple]
    ) -> Tuple[List[Dict], List[Tuple]]:
        """Remueve nodos y aristas duplicadas"""
        # Remover nodos duplicados por ID
        seen_ids = set()
        unique_nodes = []
        
        for node in nodes:
            node_id = node.get('id')
            if node_id not in seen_ids:
                seen_ids.add(node_id)
                unique_nodes.append(node)
        
        # Remover aristas duplicadas
        seen_edges = set()
        unique_edges = []
        
        for source, target, attrs in edges:
            edge_key = (source, target)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                unique_edges.append((source, target, attrs))
        
        logger.debug(
            f"Removidos {len(nodes) - len(unique_nodes)} nodos duplicados, "
            f"{len(edges) - len(unique_edges)} aristas duplicadas"
        )
        
        return unique_nodes, unique_edges
    
    def _prune_redundant_nodes(
        self,
        nodes: List[Dict],
        edges: List[Tuple]
    ) -> Tuple[List[Dict], List[Tuple]]:
        """Poda nodos redundantes (aislados o con grado 1 sin importancia)"""
        # Construir grafo de adyacencia
        adjacency = defaultdict(set)
        for source, target, _ in edges:
            adjacency[source].add(target)
            adjacency[target].add(source)
        
        # Identificar nodos a mantener
        important_nodes = set()
        
        for node in nodes:
            node_id = node.get('id')
            degree = len(adjacency[node_id])
            
            # Mantener nodos con:
            # - Grado > 1
            # - Marcados como importantes
            # - Son raíz o hoja importante
            is_important = (
                degree > 1 or
                node.get('important', False) or
                node.get('is_root', False) or
                node.get('is_leaf_important', False)
            )
            
            if is_important:
                important_nodes.add(node_id)
        
        # Filtrar nodos y aristas
        pruned_nodes = [n for n in nodes if n.get('id') in important_nodes]
        pruned_edges = [
            (s, t, a) for s, t, a in edges
            if s in important_nodes and t in important_nodes
        ]
        
        logger.debug(f"Podados {len(nodes) - len(pruned_nodes)} nodos redundantes")
        
        return pruned_nodes, pruned_edges
    
    def _aggregate_nodes(
        self,
        nodes: List[Dict],
        edges: List[Tuple]
    ) -> Tuple[List[Dict], List[Tuple]]:
        """Agrega nodos similares en clusters"""
        # Estrategia simple: agrupar por nivel/profundidad
        level_groups = defaultdict(list)
        
        for node in nodes:
            level = node.get('level', 0)
            level_groups[level].append(node)
        
        aggregated_nodes = []
        aggregated_edges = []
        node_mapping = {}  # old_id -> new_id
        
        for level, level_nodes in level_groups.items():
            if len(level_nodes) <= 5:
                # Mantener nodos individuales
                aggregated_nodes.extend(level_nodes)
                for node in level_nodes:
                    node_mapping[node['id']] = node['id']
            else:
                # Crear nodo agregado
                cluster_id = f"cluster_level_{level}"
                cluster_node = {
                    'id': cluster_id,
                    'label': f"Level {level} ({len(level_nodes)} nodes)",
                    'type': 'cluster',
                    'level': level,
                    'aggregated_count': len(level_nodes),
                    'original_nodes': [n['id'] for n in level_nodes]
                }
                aggregated_nodes.append(cluster_node)
                
                for node in level_nodes:
                    node_mapping[node['id']] = cluster_id
        
        # Remap edges
        edge_map = defaultdict(lambda: {'count': 0, 'attrs': {}})
        
        for source, target, attrs in edges:
            new_source = node_mapping.get(source, source)
            new_target = node_mapping.get(target, target)
            
            if new_source != new_target:
                edge_key = (new_source, new_target)
                edge_map[edge_key]['count'] += 1
                edge_map[edge_key]['attrs'] = attrs
        
        for (source, target), info in edge_map.items():
            attrs = info['attrs'].copy()
            attrs['aggregated_count'] = info['count']
            aggregated_edges.append((source, target, attrs))
        
        logger.debug(
            f"Agregados {len(nodes)} nodos en {len(aggregated_nodes)} clusters"
        )
        
        return aggregated_nodes, aggregated_edges
    
    def _apply_clustering(
        self,
        nodes: List[Dict],
        edges: List[Tuple]
    ) -> Tuple[List[Dict], List[Tuple], Dict]:
        """Aplica clustering jerárquico"""
        # Implementación simplificada de clustering por niveles
        clusters = self._detect_communities(nodes, edges)
        
        # Añadir información de cluster a nodos
        for node in nodes:
            cluster_id = clusters.get(node['id'], 0)
            node['cluster'] = cluster_id
            node['cluster_color'] = self._get_cluster_color(cluster_id)
        
        cluster_info = {
            'num_clusters': len(set(clusters.values())),
            'cluster_sizes': defaultdict(int)
        }
        
        for cluster_id in clusters.values():
            cluster_info['cluster_sizes'][cluster_id] += 1
        
        return nodes, edges, cluster_info
    
    def _detect_communities(
        self,
        nodes: List[Dict],
        edges: List[Tuple]
    ) -> Dict[str, int]:
        """Detecta comunidades en el grafo (algoritmo simple)"""
        # Construcción de grafo de adyacencia
        adjacency = defaultdict(set)
        for source, target, _ in edges:
            adjacency[source].add(target)
            adjacency[target].add(source)
        
        # Asignación de clusters (BFS simple)
        clusters = {}
        cluster_id = 0
        
        for node in nodes:
            node_id = node['id']
            if node_id not in clusters:
                # BFS para este componente
                queue = [node_id]
                clusters[node_id] = cluster_id
                
                while queue:
                    current = queue.pop(0)
                    for neighbor in adjacency[current]:
                        if neighbor not in clusters:
                            clusters[neighbor] = cluster_id
                            queue.append(neighbor)
                
                cluster_id += 1
        
        return clusters
    
    def _get_cluster_color(self, cluster_id: int) -> str:
        """Obtiene color para un cluster"""
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',
            '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'
        ]
        return colors[cluster_id % len(colors)]
    
    def _simplify_edges(
        self,
        nodes: List[Dict],
        edges: List[Tuple]
    ) -> List[Tuple]:
        """Simplifica aristas (remueve transitividad, etc)"""
        # Remover aristas transitivas
        node_ids = {n['id'] for n in nodes}
        adjacency = defaultdict(set)
        
        for source, target, _ in edges:
            adjacency[source].add(target)
        
        # Detectar y remover transitividad
        transitive_edges = set()
        
        for source in adjacency:
            for intermediate in adjacency[source]:
                for target in adjacency[intermediate]:
                    if target in adjacency[source] and target != source:
                        # Arista transitiva: source -> intermediate -> target
                        transitive_edges.add((source, target))
        
        # Filtrar aristas
        simplified = [
            (s, t, a) for s, t, a in edges
            if (s, t) not in transitive_edges
        ]
        
        logger.debug(f"Removidas {len(transitive_edges)} aristas transitivas")
        
        return simplified
    
    def _bundle_edges(
        self,
        nodes: List[Dict],
        edges: List[Tuple]
    ) -> List[Tuple]:
        """Agrupa aristas paralelas (edge bundling)"""
        # Agrupar aristas entre los mismos nodos
        edge_bundles = defaultdict(list)
        
        for source, target, attrs in edges:
            # Normalizar dirección para aristas no dirigidas
            key = tuple(sorted([source, target]))
            edge_bundles[key].append(attrs)
        
        bundled = []
        for (n1, n2), attrs_list in edge_bundles.items():
            # Combinar atributos
            combined_attrs = attrs_list[0].copy() if attrs_list else {}
            combined_attrs['bundle_size'] = len(attrs_list)
            combined_attrs['bundled'] = True
            
            bundled.append((n1, n2, combined_attrs))
        
        logger.debug(
            f"Agrupadas {len(edges)} aristas en {len(bundled)} bundles"
        )
        
        return bundled
    
    def _apply_lod(
        self,
        nodes: List[Dict],
        metrics: GraphMetrics
    ) -> List[Dict]:
        """Aplica Level of Detail a los nodos"""
        # Asignar nivel de detalle basado en importancia
        for node in nodes:
            # Calcular importancia (0-1)
            importance = self._calculate_node_importance(node, metrics)
            
            # Asignar LOD
            if importance > 0.7:
                node['lod'] = 'high'
                node['detail_level'] = 3
            elif importance > 0.4:
                node['lod'] = 'medium'
                node['detail_level'] = 2
            else:
                node['lod'] = 'low'
                node['detail_level'] = 1
        
        return nodes
    
    def _calculate_node_importance(
        self,
        node: Dict,
        metrics: GraphMetrics
    ) -> float:
        """Calcula la importancia de un nodo (0-1)"""
        importance = 0.5  # Base
        
        # Factores que aumentan importancia
        if node.get('is_root'):
            importance += 0.3
        if node.get('is_critical'):
            importance += 0.2
        if node.get('degree', 0) > metrics.avg_degree * 2:
            importance += 0.2
        
        return min(importance, 1.0)
    
    def optimize_recursion_tree(
        self,
        tree_data: Dict[str, Any],
        max_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Optimiza árbol de recursión específicamente
        
        Args:
            tree_data: Datos del árbol de recursión
            max_depth: Profundidad máxima a mostrar
            
        Returns:
            Árbol optimizado
        """
        if max_depth is None:
            max_depth = 10 if self.config.level == OptimizationLevel.AGGRESSIVE else 15
        
        optimized = tree_data.copy()
        
        # Podar árbol por profundidad
        if 'root' in optimized:
            optimized['root'] = self._prune_tree_depth(
                optimized['root'],
                max_depth
            )
        
        # Colapsar nodos repetitivos
        if self.config.node_aggregation:
            optimized = self._collapse_repetitive_subtrees(optimized)
        
        return optimized
    
    def _prune_tree_depth(
        self,
        node: Dict,
        max_depth: int,
        current_depth: int = 0
    ) -> Dict:
        """Poda árbol por profundidad"""
        if current_depth >= max_depth:
            # Colapsar subárbol
            return {
                **node,
                'children': [],
                'collapsed': True,
                'collapsed_subtree_size': self._count_subtree_nodes(node)
            }
        
        if 'children' in node:
            node['children'] = [
                self._prune_tree_depth(child, max_depth, current_depth + 1)
                for child in node['children']
            ]
        
        return node
    
    def _count_subtree_nodes(self, node: Dict) -> int:
        """Cuenta nodos en subárbol"""
        count = 1
        if 'children' in node:
            for child in node['children']:
                count += self._count_subtree_nodes(child)
        return count
    
    def _collapse_repetitive_subtrees(self, tree_data: Dict) -> Dict:
        """Colapsa subárboles repetitivos"""
        # Detectar patrones repetitivos y colapsarlos
        # Implementación simplificada
        return tree_data
    
    def get_optimization_recommendations(
        self,
        metrics: GraphMetrics
    ) -> List[str]:
        """Obtiene recomendaciones de optimización"""
        recommendations = []
        
        if metrics.num_nodes > 1000:
            recommendations.append(
                "Considerar usar agregación de nodos para reducir complejidad visual"
            )
        
        if metrics.density > 0.5:
            recommendations.append(
                "Grafo denso detectado: usar edge bundling para mejorar legibilidad"
            )
        
        if metrics.max_degree > 50:
            recommendations.append(
                "Nodos con alto grado detectados: considerar usar clustering"
            )
        
        if not metrics.is_sparse:
            recommendations.append(
                "Grafo no disperso: algoritmos de layout pueden ser lentos"
            )
        
        return recommendations