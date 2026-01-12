"""
Algorithm Service - Servicio de Gestión de Algoritmos

Proporciona operaciones CRUD y gestión completa de algoritmos,
incluyendo almacenamiento, búsqueda y versionado.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

from app.core.config import settings
from app.core.exceptions import (
    ValidationException,
    AlgorithmTooLargeException,
)
from app.core.parser import PseudocodeParser, parse_pseudocode
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Enums
class AlgorithmStatus(str, Enum):
    """Estados de un algoritmo"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"

class AlgorithmCategory(str, Enum):
    """Categorías de algoritmos"""
    SORTING = "sorting"
    SEARCHING = "searching"
    GRAPH = "graph"
    DYNAMIC_PROGRAMMING = "dynamic_programming"
    GREEDY = "greedy"
    DIVIDE_AND_CONQUER = "divide_and_conquer"
    BACKTRACKING = "backtracking"
    RECURSION = "recursion"
    OTHER = "other"

# DTOs
@dataclass
class AlgorithmMetadata:
    """Metadata de un algoritmo"""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[AlgorithmCategory] = None
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: AlgorithmStatus = AlgorithmStatus.DRAFT
    version: int = 1

    # Estadísticas
    lines_of_code: int = 0
    analysis_count: int = 0
    last_analyzed: Optional[datetime] = None

@dataclass
class AlgorithmCreateRequest:
    """Request para crear un algoritmo"""
    code: str
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[AlgorithmCategory] = None
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None

@dataclass
class AlgorithmUpdateRequest:
    """Request para actualizar un algoritmo"""
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[AlgorithmCategory] = None
    tags: Optional[List[str]] = None
    status: Optional[AlgorithmStatus] = None

@dataclass
class AlgorithmSearchCriteria:
    """Criterios de búsqueda de algoritmos"""
    name: Optional[str] = None
    category: Optional[AlgorithmCategory] = None
    tags: Optional[List[str]] = None
    status: Optional[AlgorithmStatus] = None
    author: Optional[str] = None
    limit: int = 10
    offset: int = 0

@dataclass
class StoredAlgorithm:
    """Algoritmo almacenado completo"""
    metadata: AlgorithmMetadata
    code: str
    file_path: Optional[Path] = None

# Service
class AlgorithmService:
    """
    Servicio de gestión de algoritmos.

    Proporciona operaciones CRUD y gestión completa de algoritmos,
    incluyendo validación, almacenamiento y búsqueda.

    Example:
        >>> service = AlgorithmService()
        >>> request = AlgorithmCreateRequest(
        ...     code="algorithm test(n)\\nbegin\\n  x <- 1\\nend",
        ...     name="Test Algorithm"
        ... )
        >>> algorithm = await service.create(request)
        >>> print(algorithm.metadata.id)
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        parser: Optional[PseudocodeParser] = None
    ):
        """
        Inicializa el servicio.

        Args:
            storage_path: Ruta para almacenar algoritmos (por defecto: settings.ALGORITHMS_PATH)
            parser: Parser personalizado (por defecto: PseudocodeParser())
        """
        self.storage_path = storage_path or settings.ALGORITHMS_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.parser = parser or PseudocodeParser()

        # Índice en memoria (en producción, usar base de datos)
        self._index: Dict[str, AlgorithmMetadata] = {}

        logger.info(f"AlgorithmService inicializado - Storage: {self.storage_path}")

    # CRUD Operations
    async def create(self, request: AlgorithmCreateRequest) -> StoredAlgorithm:
        """
        Crea un nuevo algoritmo.

        Args:
            request: Datos del algoritmo a crear

        Returns:
            StoredAlgorithm: Algoritmo creado

        Raises:
            ValidationException: Si el código no es válido
            AlgorithmTooLargeException: Si el código excede el tamaño máximo
        """
        logger.info("Creando nuevo algoritmo")

        # Validar tamaño
        self._validate_code_size(request.code)

        # Parsear para obtener nombre si no se proporciona
        try:
            ast = self.parser.parse(request.code, validate=True)
            algorithm_name = request.name or ast.algorithm.name
        except Exception as e:
            logger.error(f"Error parseando algoritmo: {e}")
            raise ValidationException(f"Código inválido: {e}")

        # Crear metadata
        algorithm_id = str(uuid4())
        metadata = AlgorithmMetadata(
            id=algorithm_id,
            name=algorithm_name,
            description=request.description,
            category=request.category,
            tags=request.tags,
            author=request.author,
            lines_of_code=len(request.code.splitlines())
        )

        # Guardar en disco
        file_path = await self._save_to_disk(algorithm_id, request.code, metadata)

        # Agregar al índice
        self._index[algorithm_id] = metadata

        logger.info(f"Algoritmo creado: {algorithm_id} - {algorithm_name}")

        return StoredAlgorithm(
            metadata=metadata,
            code=request.code,
            file_path=file_path
        )

    async def get(self, algorithm_id: str) -> Optional[StoredAlgorithm]:
        """
        Obtiene un algoritmo por ID.

        Args:
            algorithm_id: ID del algoritmo

        Returns:
            StoredAlgorithm: Algoritmo encontrado o None
        """
        metadata = self._index.get(algorithm_id)
        if not metadata:
            logger.warning(f"Algoritmo no encontrado: {algorithm_id}")
            return None

        # Leer código del disco
        file_path = self._get_file_path(algorithm_id)
        if not file_path.exists():
            logger.error(f"Archivo no encontrado: {file_path}")
            return None

        code = file_path.read_text(encoding='utf-8')

        return StoredAlgorithm(
            metadata=metadata,
            code=code,
            file_path=file_path
        )

    async def update(
        self,
        algorithm_id: str,
        request: AlgorithmUpdateRequest
    ) -> Optional[StoredAlgorithm]:
        """
        Actualiza un algoritmo existente.

        Args:
            algorithm_id: ID del algoritmo
            request: Datos a actualizar

        Returns:
            StoredAlgorithm: Algoritmo actualizado o None
        """
        # Obtener algoritmo existente
        existing = await self.get(algorithm_id)
        if not existing:
            return None

        logger.info(f"Actualizando algoritmo: {algorithm_id}")

        # Actualizar código si se proporciona
        new_code = existing.code
        if request.code:
            self._validate_code_size(request.code)

            # Validar parseando
            try:
                self.parser.parse(request.code, validate=True)
                new_code = request.code
            except Exception as e:
                raise ValidationException(f"Código inválido: {e}")

        # Actualizar metadata
        metadata = existing.metadata

        if request.name is not None:
            metadata.name = request.name
        if request.description is not None:
            metadata.description = request.description
        if request.category is not None:
            metadata.category = request.category
        if request.tags is not None:
            metadata.tags = request.tags
        if request.status is not None:
            metadata.status = request.status

        metadata.updated_at = datetime.utcnow()
        metadata.version += 1

        if request.code:
            metadata.lines_of_code = len(new_code.splitlines())

        # Guardar cambios
        file_path = await self._save_to_disk(algorithm_id, new_code, metadata)

        # Actualizar índice
        self._index[algorithm_id] = metadata

        logger.info(f"Algoritmo actualizado: {algorithm_id} - Version {metadata.version}")

        return StoredAlgorithm(
            metadata=metadata,
            code=new_code,
            file_path=file_path
        )

    async def delete(self, algorithm_id: str) -> bool:
        """
        Elimina un algoritmo.

        Args:
            algorithm_id: ID del algoritmo

        Returns:
            bool: True si se eliminó, False si no existía
        """
        if algorithm_id not in self._index:
            return False

        logger.info(f"Eliminando algoritmo: {algorithm_id}")

        # Eliminar del disco
        file_path = self._get_file_path(algorithm_id)
        if file_path.exists():
            file_path.unlink()

        # Eliminar metadata file si existe
        metadata_path = file_path.with_suffix('.json')
        if metadata_path.exists():
            metadata_path.unlink()

        # Eliminar del índice
        del self._index[algorithm_id]

        logger.info(f"Algoritmo eliminado: {algorithm_id}")
        return True

    async def search(
        self,
        criteria: AlgorithmSearchCriteria
    ) -> List[AlgorithmMetadata]:
        """
        Busca algoritmos según criterios.

        Args:
            criteria: Criterios de búsqueda

        Returns:
            List[AlgorithmMetadata]: Algoritmos que cumplen criterios
        """
        results = list(self._index.values())

        # Filtrar por criterios
        if criteria.name:
            results = [
                a for a in results
                if criteria.name.lower() in a.name.lower()
            ]

        if criteria.category:
            results = [
                a for a in results
                if a.category == criteria.category
            ]

        if criteria.status:
            results = [
                a for a in results
                if a.status == criteria.status
            ]

        if criteria.author:
            results = [
                a for a in results
                if a.author and criteria.author.lower() in a.author.lower()
            ]

        if criteria.tags:
            results = [
                a for a in results
                if any(tag in a.tags for tag in criteria.tags)
            ]

        # Ordenar por fecha de creación (más recientes primero)
        results.sort(key=lambda x: x.created_at, reverse=True)

        # Paginación
        start = criteria.offset
        end = start + criteria.limit

        return results[start:end]

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[AlgorithmMetadata]:
        """
        Lista todos los algoritmos.

        Args:
            limit: Número máximo de resultados
            offset: Desplazamiento para paginación
            
        Returns:
            List[AlgorithmMetadata]: Lista de metadata
        """
        all_algorithms = list(self._index.values())
        all_algorithms.sort(key=lambda x: x.created_at, reverse=True)

        return all_algorithms[offset:offset + limit]

    # Helper Methods
    def _validate_code_size(self, code: str) -> None:
        """
        Valida el tamaño del código.

        Args:
            code: Código a validar

        Raises:
            AlgorithmTooLargeException: Si excede límites
        """
        # Validar longitud
        if len(code) > settings.MAX_ALGORITHM_SIZE_KB * 1024:
            raise AlgorithmTooLargeException(
                len(code),
                settings.MAX_ALGORITHM_SIZE_KB * 1024
            )

        # Validar líneas
        lines = code.splitlines()
        if len(lines) > settings.MAX_ALGORITHM_LINES:
            raise ValidationException(
                f"Demasiadas líneas: {len(lines)} (máximo: {settings.MAX_ALGORITHM_LINES})"
            )

    def _get_file_path(self, algorithm_id: str) -> Path:
        """Obtiene la ruta del archivo del algoritmo"""
        return self.storage_path / f"{algorithm_id}.txt"

    async def _save_to_disk(
        self,
        algorithm_id: str,
        code: str,
        metadata: AlgorithmMetadata
    ) -> Path:
        """
        Guarda el algoritmo en disco.

        Args:
            algorithm_id: ID del algoritmo
            code: Código a guardar
            metadata: Metadata del algoritmo

        Returns:
            Path: Ruta del archivo guardado
        """
        file_path = self._get_file_path(algorithm_id)

        # Guardar código
        file_path.write_text(code, encoding='utf-8')

        # Guardar metadata en archivo JSON (opcional)
        # metadata_path = file_path.with_suffix('.json')
        # metadata_path.write_text(
        #     json.dumps(asdict(metadata), default=str, indent=2),
        #     encoding='utf-8'
        # )

        return file_path

    # Utility Methods
    async def validate_code(self, code: str) -> bool:
        """
        Valida código sin guardarlo.

        Args:
            code: Código a validar

        Returns:
            bool: True si es válido

        Raises:
            ValidationException: Si no es válido
        """
        self._validate_code_size(code)

        try:
            self.parser.parse(code, validate=True)
            return True
        except Exception as e:
            raise ValidationException(f"Código inválido: {e}")

    async def increment_analysis_count(self, algorithm_id: str) -> None:
        """
        Incrementa el contador de análisis de un algoritmo.

        Args:
            algorithm_id: ID del algoritmo
        """
        metadata = self._index.get(algorithm_id)
        if metadata:
            metadata.analysis_count += 1
            metadata.last_analyzed = datetime.utcnow()
            logger.debug(f"Contador de análisis incrementado: {algorithm_id}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio.

        Returns:
            Dict: Estadísticas
        """
        total = len(self._index)
        by_category = {}
        by_status = {}

        for metadata in self._index.values():
            # Por categoría
            cat = metadata.category.value if metadata.category else "uncategorized"
            by_category[cat] = by_category.get(cat, 0) + 1

            # Por estado
            status = metadata.status.value
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_algorithms": total,
            "by_category": by_category,
            "by_status": by_status,
            "storage_path": str(self.storage_path),
        }