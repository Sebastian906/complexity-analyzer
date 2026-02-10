"""
Usage Analyzer - Análisis de Uso de Estructuras de Datos

Analiza cómo se utilizan las estructuras detectadas en el algoritmo,
incluyendo frecuencia de operaciones, patrones de acceso y métricas.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import Counter

from app.core.parser.ast_nodes import ProgramNode, ASTNode
from app.core.data_structures.base_structure import StructureMatch
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class OperationFrequency:
    """Frecuencia de una operación sobre una estructura"""
    operation: str
    count: int
    complexity: str
    examples: List[str] = field(default_factory=list)

@dataclass
class StructureUsage:
    """
    Análisis de uso de una estructura de datos.

    Contiene métricas sobre cómo se utiliza la estructura:
    - Frecuencia de operaciones
    - Patrones de acceso
    - Impacto en complejidad total
    """
    structure_match: StructureMatch

    # Frecuencias de operaciones
    operation_frequencies: List[OperationFrequency] = field(default_factory=list)

    # Operación más frecuente
    most_frequent_operation: Optional[str] = None

    # Patrón de acceso dominante
    access_pattern: str = "unknown"

    # Impacto en complejidad
    complexity_impact: Dict[str, str] = field(default_factory=dict)

    # Métricas
    total_operations: int = 0
    unique_operations: int = 0

    # Recomendaciones
    recommendations: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calcula métricas derivadas"""
        if self.operation_frequencies:
            self.total_operations = sum(
                op.count for op in self.operation_frequencies
            )
            self.unique_operations = len(self.operation_frequencies)

            # Operación más frecuente
            max_op = max(
                self.operation_frequencies,
                key=lambda x: x.count
            )
            self.most_frequent_operation = max_op.operation

    def get_summary(self) -> str:
        """Retorna resumen legible del uso"""
        summary_parts = [
            f"Estructura: {self.structure_match.structure_name}",
            f"Total operaciones: {self.total_operations}",
        ]

        if self.most_frequent_operation:
            summary_parts.append(
                f"Operación dominante: {self.most_frequent_operation}"
            )

        if self.access_pattern != "unknown":
            summary_parts.append(f"Patrón de acceso: {self.access_pattern}")

        if self.recommendations:
            summary_parts.append(
                f"Recomendaciones: {len(self.recommendations)}"
            )

        return "\n".join(summary_parts)

class UsageAnalyzer:
    """
    Analizador de uso de estructuras de datos.

    Examina el AST para determinar cómo se utilizan las estructuras
    detectadas y proporciona análisis detallado.
    """

    def __init__(self):
        """Inicializa el analizador"""
        logger.info("UsageAnalyzer inicializado")

    def analyze(
        self,
        ast: ProgramNode,
        structure_match: StructureMatch
    ) -> StructureUsage:
        """
        Analiza el uso de una estructura específica.

        Args:
            ast: Abstract Syntax Tree del algoritmo
            structure_match: Estructura detectada a analizar

        Returns:
            StructureUsage con análisis completo

        Example:
            >>> analyzer = UsageAnalyzer()
            >>> usage = analyzer.analyze(ast, structure_match)
            >>> print(usage.get_summary())
        """
        logger.info(
            f"Analizando uso de {structure_match.structure_name}"
        )

        # Recolectar operaciones
        operation_counts = self._count_operations(
            ast,
            structure_match
        )

        # Crear OperationFrequency para cada operación
        op_frequencies = []
        for op_name, count in operation_counts.items():
            # Buscar complejidad en operation_complexities
            complexity = self._find_complexity(
                structure_match,
                op_name
            )
            
            # Extraer ejemplos del código para esta operación
            examples = self._extract_operation_examples(
                structure_match.operations,
                op_name
            )

            op_frequencies.append(
                OperationFrequency(
                    operation=op_name,
                    count=count,
                    complexity=complexity,
                    examples=examples
                )
            )

        # Determinar patrón de acceso
        access_pattern = self._determine_access_pattern(
            structure_match,
            operation_counts
        )

        # Calcular impacto en complejidad
        complexity_impact = self._calculate_complexity_impact(
            structure_match,
            op_frequencies
        )

        # Generar recomendaciones
        recommendations = self._generate_recommendations(
            structure_match,
            op_frequencies,
            access_pattern
        )

        usage = StructureUsage(
            structure_match=structure_match,
            operation_frequencies=op_frequencies,
            access_pattern=access_pattern,
            complexity_impact=complexity_impact,
            recommendations=recommendations
        )

        logger.info(
            f"Análisis completado: {usage.total_operations} operaciones"
        )

        return usage

    def _count_operations(
        self,
        ast: ProgramNode,
        structure_match: StructureMatch
    ) -> Dict[str, int]:
        """
        Cuenta frecuencia de cada operación.

        Args:
            ast: AST del algoritmo
            structure_match: Estructura a analizar

        Returns:
            Dict con {operación: frecuencia}
        """
        # Extraer operaciones del structure_match
        operations = structure_match.operations

        # Contar frecuencia de cada tipo
        operation_types = []
        for op in operations:
            # Extraer tipo de operación del string
            # Ej: "Acceso: A[i]" -> "Acceso"
            op_type = op.split(":")[0].strip() if ":" in op else op
            operation_types.append(op_type)

        return dict(Counter(operation_types))

    def _find_complexity(
        self,
        structure_match: StructureMatch,
        operation_name: str
    ) -> str:
        """
        Encuentra la complejidad de una operación.

        Args:
            structure_match: Match con complexities
            operation_name: Nombre de la operación

        Returns:
            String con complejidad (ej: "O(1)")
        """
        for op_complex in structure_match.operation_complexities:
            if operation_name.lower() in op_complex.operation.lower():
                return op_complex.worst_case

        return "O(?)"  # Desconocida

    def _determine_access_pattern(
        self,
        structure_match: StructureMatch,
        operation_counts: Dict[str, int]
    ) -> str:
        """
        Determina el patrón de acceso dominante.

        Args:
            structure_match: Estructura analizada
            operation_counts: Frecuencias de operaciones

        Returns:
            Patrón identificado (sequential, random, mixed)
        """
        structure_type = structure_match.structure_type.value

        # Patrones por tipo de estructura
        if structure_type == "array":
            # Si hay muchas iteraciones, es secuencial
            if "Iteración" in operation_counts:
                return "sequential"
            # Si hay accesos directos, es aleatorio
            if "Acceso" in operation_counts:
                return "random_access"
            return "mixed"

        elif structure_type == "stack":
            # Pilas son secuenciales LIFO
            return "sequential_lifo"

        elif structure_type == "queue":
            # Colas son secuenciales FIFO
            return "sequential_fifo"

        elif structure_type == "tree":
            # Árboles típicamente traversal
            return "tree_traversal"

        elif structure_type == "graph":
            # Grafos típicamente BFS/DFS
            return "graph_traversal"

        return "unknown"

    def _calculate_complexity_impact(
        self,
        structure_match: StructureMatch,
        op_frequencies: List[OperationFrequency]
    ) -> Dict[str, str]:
        """
        Calcula el impacto de la estructura en la complejidad total.

        Args:
            structure_match: Estructura analizada
            op_frequencies: Frecuencias de operaciones

        Returns:
            Dict con impactos por categoría
        """
        impact = {}

        # Operación dominante
        if op_frequencies:
            dominant = max(op_frequencies, key=lambda x: x.count)
            impact["dominant_operation"] = dominant.operation
            impact["dominant_complexity"] = dominant.complexity

        # Complejidad espacial
        impact["space_complexity"] = self._estimate_space_impact(
            structure_match
        )

        return impact

    def _estimate_space_impact(
        self,
        structure_match: StructureMatch
    ) -> str:
        """
        Estima impacto espacial de la estructura.

        Args:
            structure_match: Estructura analizada

        Returns:
            Complejidad espacial estimada
        """
        structure_type = structure_match.structure_type.value

        # Estimaciones por tipo
        space_estimates = {
            "array": "O(n)",
            "stack": "O(n)",
            "queue": "O(n)",
            "linked_list": "O(n)",
            "dictionary": "O(n)",
            "tree": "O(n)",
            "graph": "O(V + E)",
            "hash_table": "O(n)"
        }

        return space_estimates.get(structure_type, "O(n)")

    def _generate_recommendations(
        self,
        structure_match: StructureMatch,
        op_frequencies: List[OperationFrequency],
        access_pattern: str
    ) -> List[str]:
        """
        Genera recomendaciones basadas en el uso.

        Args:
            structure_match: Estructura analizada
            op_frequencies: Frecuencias de operaciones
            access_pattern: Patrón de acceso detectado

        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        structure_type = structure_match.structure_type.value

        # Recomendaciones por tipo y patrón
        if structure_type == "array":
            if access_pattern == "sequential":
                recommendations.append(
                    "Acceso secuencial óptimo para arrays"
                )
            elif access_pattern == "random_access":
                recommendations.append(
                    "Acceso aleatorio eficiente con arrays (O(1))"
                )

        elif structure_type == "stack":
            recommendations.append(
                "Estructura óptima para operaciones LIFO"
            )

        elif structure_type == "linked_list":
            # Verificar si hay muchas búsquedas
            search_ops = [
                op for op in op_frequencies
                if "búsqueda" in op.operation.lower()
            ]
            if search_ops and search_ops[0].count > 5:
                recommendations.append(
                    "Considerar usar array o hash table para búsquedas frecuentes (O(n) actual)"
                )

        # Recomendación general sobre complejidad
        if op_frequencies:
            worst_complexity = max(
                (op.complexity for op in op_frequencies),
                key=lambda c: self._complexity_order(c)
            )
            if worst_complexity not in ["O(1)", "O(log n)"]:
                recommendations.append(
                    f"Operación más costosa: {worst_complexity}. "
                    "Considerar optimización si es cuello de botella."
                )

        return recommendations
    
    def _extract_operation_examples(
        self,
        operations: List[str],
        operation_name: str,
        max_examples: int = 3
    ) -> List[str]:
        """
        Extrae ejemplos del código para una operación específica.
        
        Args:
            operations: Lista de operaciones detectadas (strings)
            operation_name: Nombre de la operación a buscar
            max_examples: Máximo número de ejemplos a extraer
        
        Returns:
            Lista de strings con ejemplos del código
        """
        examples = []
        
        for op in operations:
            # Las operaciones tienen formato "Tipo: detalle"
            # Por ejemplo: "Acceso: A[i]", "Iteración: for i ← 1 to n"
            if ":" in op:
                op_type, op_detail = op.split(":", 1)
                op_type = op_type.strip()
                op_detail = op_detail.strip()
                
                if op_type.lower() == operation_name.lower():
                    examples.append(op_detail)
                    if len(examples) >= max_examples:
                        break
            else:
                # Si no tiene formato, buscar coincidencia directa
                if operation_name.lower() in op.lower():
                    examples.append(op)
                    if len(examples) >= max_examples:
                        break
        
        return examples

    def _complexity_order(self, complexity: str) -> int:
        """Ordena complejidades para comparación"""
        order = {
            "O(1)": 0,
            "O(log n)": 1,
            "O(n)": 2,
            "O(n log n)": 3,
            "O(n²)": 4,
            "O(n^2)": 4,
            "O(2^n)": 5,
            "O(n!)": 6,
        }
        return order.get(complexity, 10)

# Helper function para uso rápido

def analyze_structure_usage(
    ast: ProgramNode,
    structure_match: StructureMatch
) -> StructureUsage:
    """
    Helper function para analizar uso rápidamente.

    Args:
        ast: Abstract Syntax Tree del algoritmo
        structure_match: Estructura detectada

    Returns:
        StructureUsage con análisis completo

    Example:
        >>> from app.core.data_structures import (
        ...     identify_structures,
        ...     analyze_structure_usage
        ... )
        >>> 
        >>> result = identify_structures(ast)
        >>> if result.primary_structure:
        ...     usage = analyze_structure_usage(ast, result.primary_structure)
        ...     print(usage.get_summary())
    """
    analyzer = UsageAnalyzer()
    return analyzer.analyze(ast, structure_match)