"""
Structure Identifier - Identificador Principal de Estructuras de Datos

Orquesta todos los detectores de estructuras y proporciona la interfaz
principal para la detección.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict

from app.core.parser.ast_nodes import ProgramNode
from app.core.data_structures.base_structure import (
    BaseStructureDetector,
    StructureMatch,
    StructureType
)

# Importar todos los detectores
from app.core.data_structures.detectors.array_detector import ArrayDetector
from app.core.data_structures.detectors.stack_detector import StackDetector
from app.core.data_structures.detectors.queue_detector import QueueDetector
from app.core.data_structures.detectors.linked_list_detector import LinkedListDetector
from app.core.data_structures.detectors.dictionary_detector import DictionaryDetector
from app.core.data_structures.detectors.tree_detector import TreeDetector
from app.core.data_structures.detectors.graph_detector import GraphDetector
from app.core.data_structures.detectors.hash_table_detector import HashTableDetector

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class StructureDetectionResult:
    """
    Resultado completo de la detección de estructuras.

    Contiene todas las estructuras detectadas con sus confianzas,
    la estructura principal y un resumen general.
    """
    # Estructuras detectadas
    structures_found: List[StructureMatch] = field(default_factory=list)

    # Estructura principal (mayor confianza)
    primary_structure: Optional[StructureMatch] = None

    # Todas las estructuras detectadas (incluso con baja confianza)
    all_structures: List[StructureMatch] = field(default_factory=list)

    # Resumen
    summary: str = ""

    # Metadata
    metadata: Dict = field(default_factory=dict)

    # Contadores
    structure_count: int = 0
    total_variables: int = 0

    def __post_init__(self):
        """Calcula estadísticas"""
        self.structure_count = len(self.structures_found)

        # Contar variables únicas
        all_vars = set()
        for struct in self.structures_found:
            all_vars.update(struct.variables)
        self.total_variables = len(all_vars)

        # Generar resumen si no existe
        if not self.summary:
            self.summary = self._generate_summary()

    def _generate_summary(self) -> str:
        """Genera un resumen legible"""
        if not self.structures_found:
            return "No se detectaron estructuras de datos."

        parts = []

        if self.primary_structure:
            parts.append(
                f"Estructura principal: {self.primary_structure.structure_name} "
                f"(confianza: {self.primary_structure.confidence:.2%})"
            )

        if len(self.structures_found) > 1:
            other_names = [
                s.structure_name for s in self.structures_found[1:4]
            ]
            parts.append(f"Otras estructuras: {', '.join(other_names)}")

        parts.append(
            f"Total: {self.structure_count} estructura(s) en "
            f"{self.total_variables} variable(s)"
        )

        return ". ".join(parts)

class StructureIdentifier:
    """
    Identificador principal de estructuras de datos.

    Orquesta todos los detectores específicos y proporciona
    la interfaz unificada para detección.
    """

    def __init__(self):
        """Inicializa todos los detectores"""
        self.detectors: List[BaseStructureDetector] = [
            ArrayDetector(),
            StackDetector(),
            QueueDetector(),
            LinkedListDetector(),
            DictionaryDetector(),
            TreeDetector(),
            GraphDetector(),
            HashTableDetector(),
        ]

        logger.info(f"StructureIdentifier inicializado con {len(self.detectors)} detectores")

    def identify(
        self,
        ast: ProgramNode,
        min_confidence: float = 0.3
    ) -> StructureDetectionResult:
        """
        Identifica todas las estructuras de datos en el AST.

        Args:
            ast: Abstract Syntax Tree del algoritmo
            min_confidence: Umbral mínimo de confianza (0.0-1.0)

        Returns:
            StructureDetectionResult con todas las detecciones

        Example:
            >>> from app.core.parser import parse_pseudocode
            >>> ast = parse_pseudocode(code)
            >>> identifier = StructureIdentifier()
            >>> result = identifier.identify(ast)
            >>> print(result.summary)
        """
        logger.info("Iniciando identificación de estructuras")

        all_matches = []

        # Ejecutar cada detector
        for detector in self.detectors:
            try:
                match = detector.detect(ast)
                if match:
                    all_matches.append(match)
                    logger.debug(
                        f"{detector.structure_name}: "
                        f"confianza={match.confidence:.2%}"
                    )
            except Exception as e:
                logger.error(
                    f"Error en {detector.__class__.__name__}: {e}",
                    exc_info=True
                )

        # Filtrar por confianza mínima
        confident_matches = [
            m for m in all_matches if m.confidence >= min_confidence
        ]

        # Ordenar por confianza descendente
        confident_matches.sort(key=lambda m: m.confidence, reverse=True)

        # Identificar estructura principal
        primary = confident_matches[0] if confident_matches else None

        # Construir metadata
        metadata = {
            "total_detectors": len(self.detectors),
            "structures_evaluated": len(all_matches),
            "structures_above_threshold": len(confident_matches),
            "min_confidence_threshold": min_confidence,
            "confidence_range": self._get_confidence_range(confident_matches)
        }

        result = StructureDetectionResult(
            structures_found=confident_matches,
            primary_structure=primary,
            all_structures=all_matches,
            metadata=metadata
        )

        logger.info(
            f"Identificación completada: {result.structure_count} estructura(s) detectada(s)"
        )

        return result

    def identify_specific(
        self,
        ast: ProgramNode,
        structure_type: StructureType
    ) -> Optional[StructureMatch]:
        """
        Identifica una estructura específica.

        Args:
            ast: Abstract Syntax Tree
            structure_type: Tipo de estructura a buscar

        Returns:
            StructureMatch si se encuentra, None si no

        Example:
            >>> result = identifier.identify_specific(ast, StructureType.STACK)
            >>> if result:
            ...     print(f"Pila detectada: {result.confidence:.2%}")
        """
        # Buscar detector correspondiente
        for detector in self.detectors:
            if detector.structure_type == structure_type:
                try:
                    return detector.detect(ast)
                except Exception as e:
                    logger.error(f"Error detectando {structure_type.value}: {e}")
                    return None

        logger.warning(f"No existe detector para {structure_type.value}")
        return None

    def get_available_structures(self) -> List[Dict]:
        """
        Retorna lista de estructuras detectables.

        Returns:
            Lista de diccionarios con info de cada estructura

        Example:
            >>> structures = identifier.get_available_structures()
            >>> for s in structures:
            ...     print(f"{s['name']}: {s['description']}")
        """
        return [
            {
                "type": d.structure_type.value,
                "name": d.structure_name,
                "description": d.description
            }
            for d in self.detectors
        ]

    def _get_confidence_range(self, matches: List[StructureMatch]) -> Dict:
        """Calcula rango de confianzas"""
        if not matches:
            return {"min": 0.0, "max": 0.0, "avg": 0.0}

        confidences = [m.confidence for m in matches]
        return {
            "min": min(confidences),
            "max": max(confidences),
            "avg": sum(confidences) / len(confidences)
        }

# Helper function para uso rápido

def identify_structures(
    ast: ProgramNode,
    min_confidence: float = 0.3
) -> StructureDetectionResult:
    """
    Helper function para identificar estructuras rápidamente.

    Args:
        ast: Abstract Syntax Tree del algoritmo
        min_confidence: Umbral mínimo de confianza

    Returns:
        StructureDetectionResult con todas las detecciones

    Example:
        >>> from app.core.parser import parse_pseudocode
        >>> from app.core.data_structures import identify_structures
        >>> 
        >>> ast = parse_pseudocode(code)
        >>> result = identify_structures(ast)
        >>> print(result.summary)
    """
    identifier = StructureIdentifier()
    return identifier.identify(ast, min_confidence)