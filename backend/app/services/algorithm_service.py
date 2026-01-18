"""
Algorithm Service - Servicio de Gestión de Algoritmos

Proporciona operaciones CRUD y gestión completa de algoritmos,
incluyendo almacenamiento, búsqueda y versionado.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Any
from uuid import uuid4

from app.core.config import settings
from app.core.exceptions import (
    ValidationException,
    AlgorithmTooLargeException,
)
from app.core.parser import PseudocodeParser, parse_pseudocode
from app.schemas import (
    # Algorithm Schemas
    AlgorithmCreate,
    AlgorithmUpdate,
    Algorithm,
    AlgorithmMetadata,
    AlgorithmInfo,
    AlgorithmParameter,
    AlgorithmCategory,
    AlgorithmComplexityClass,
    AlgorithmSearchCriteria,
    AlgorithmSortBy,
    
    # Response Schemas
    AlgorithmResponse,
    AlgorithmListResponse,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class AlgorithmService:
    """
    Servicio de gestión de algoritmos refactorizado.

    Utiliza schemas de Pydantic para DTOs y validación.
    
    Example:
        >>> service = AlgorithmService()
        >>> request = AlgorithmCreate(
        ...     name="Bubble Sort",
        ...     code="algorithm bubbleSort(A[n])\\nbegin\\n...\\nend",
        ...     category=AlgorithmCategory.SORTING
        ... )
        >>> response = await service.create(request)
        >>> print(response.algorithm.id)
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        parser: Optional[PseudocodeParser] = None
    ):
        """
        Inicializa el servicio.

        Args:
            storage_path: Ruta para almacenar algoritmos
            parser: Parser personalizado
        """
        self.storage_path = storage_path or settings.ALGORITHMS_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.parser = parser or PseudocodeParser()

        # Índice en memoria (migrar a MongoDB en producción)
        self._algorithms: dict[str, Algorithm] = {}

        logger.info(f"AlgorithmService inicializado - Storage: {self.storage_path}")

    # CRUD Operations
    async def create(self, request: AlgorithmCreate) -> AlgorithmResponse:
        """
        Crea un nuevo algoritmo.

        Args:
            request: Datos del algoritmo (AlgorithmCreate schema)

        Returns:
            AlgorithmResponse: Respuesta con el algoritmo creado

        Raises:
            ValidationException: Si el código no es válido
            AlgorithmTooLargeException: Si excede límites
        """
        logger.info(f"Creando algoritmo: {request.name}")

        # Validar tamaño del código
        self._validate_code_size(request.code)

        # Parsear para validar sintaxis y extraer información
        try:
            ast = self.parser.parse(request.code, validate=True)
        except Exception as e:
            logger.error(f"Error parseando algoritmo: {e}")
            raise ValidationException(f"Código inválido: {e}")

        # Extraer información del AST
        algorithm_info = self._extract_algorithm_info(ast)

        # Generar ID único
        algorithm_id = str(uuid4())

        # Crear objeto Algorithm
        now = datetime.utcnow()
        algorithm = Algorithm(
            id=algorithm_id,
            name=request.name,
            description=request.description,
            category=request.category,
            tags=request.tags,
            language=request.language,
            code=request.code,
            info=algorithm_info,
            created_at=now,
            updated_at=now,
            analyzed=False,
            analysis_count=0,
            complexity_class=None,
            big_o=None,
        )

        # Guardar en disco
        await self._save_to_disk(algorithm)

        # Agregar al índice
        self._algorithms[algorithm_id] = algorithm

        logger.info(f"Algoritmo creado: {algorithm_id} - {request.name}")

        return AlgorithmResponse(
            success=True,
            message="Algoritmo creado exitosamente",
            algorithm=algorithm
        )

    async def get(self, algorithm_id: str) -> Optional[AlgorithmResponse]:
        """
        Obtiene un algoritmo por ID.

        Args:
            algorithm_id: ID del algoritmo

        Returns:
            AlgorithmResponse o None si no existe
        """
        algorithm = self._algorithms.get(algorithm_id)
        
        if not algorithm:
            logger.warning(f"Algoritmo no encontrado: {algorithm_id}")
            return None

        return AlgorithmResponse(
            success=True,
            message="Algoritmo recuperado exitosamente",
            algorithm=algorithm
        )

    async def update(
        self,
        algorithm_id: str,
        request: AlgorithmUpdate
    ) -> Optional[AlgorithmResponse]:
        """
        Actualiza un algoritmo existente.

        Args:
            algorithm_id: ID del algoritmo
            request: Datos a actualizar (AlgorithmUpdate schema)

        Returns:
            AlgorithmResponse o None si no existe
        """
        existing = self._algorithms.get(algorithm_id)
        if not existing:
            logger.warning(f"Algoritmo no encontrado para actualizar: {algorithm_id}")
            return None

        logger.info(f"Actualizando algoritmo: {algorithm_id}")

        # Actualizar código si se proporciona
        new_code = existing.code
        new_info = existing.info

        if request.code:
            self._validate_code_size(request.code)

            try:
                ast = self.parser.parse(request.code, validate=True)
                new_code = request.code
                new_info = self._extract_algorithm_info(ast)
            except Exception as e:
                raise ValidationException(f"Código inválido: {e}")

        # Actualizar campos
        updated_algorithm = Algorithm(
            id=existing.id,
            name=request.name if request.name is not None else existing.name,
            description=request.description if request.description is not None else existing.description,
            category=request.category if request.category is not None else existing.category,
            tags=request.tags if request.tags is not None else existing.tags,
            language=request.language if request.language is not None else existing.language,
            code=new_code,
            info=new_info,
            created_at=existing.created_at,
            updated_at=datetime.utcnow(),
            analyzed=existing.analyzed,
            analysis_count=existing.analysis_count,
            complexity_class=existing.complexity_class,
            big_o=existing.big_o,
        )

        # Guardar cambios
        await self._save_to_disk(updated_algorithm)
        self._algorithms[algorithm_id] = updated_algorithm

        logger.info(f"Algoritmo actualizado: {algorithm_id}")

        return AlgorithmResponse(
            success=True,
            message="Algoritmo actualizado exitosamente",
            algorithm=updated_algorithm
        )

    async def delete(self, algorithm_id: str) -> bool:
        """
        Elimina un algoritmo.

        Args:
            algorithm_id: ID del algoritmo

        Returns:
            bool: True si se eliminó, False si no existía
        """
        if algorithm_id not in self._algorithms:
            logger.warning(f"Algoritmo no encontrado para eliminar: {algorithm_id}")
            return False

        logger.info(f"Eliminando algoritmo: {algorithm_id}")

        # Eliminar del disco
        file_path = self._get_file_path(algorithm_id)
        if file_path.exists():
            file_path.unlink()

        # Eliminar del índice
        del self._algorithms[algorithm_id]

        logger.info(f"Algoritmo eliminado: {algorithm_id}")
        return True

    async def search(
        self,
        request: AlgorithmSearchCriteria
    ) -> AlgorithmListResponse:
        """
        Busca algoritmos según criterios.

        Args:
            request: Criterios de búsqueda (AlgorithmSearchCriteria schema)

        Returns:
            AlgorithmListResponse: Lista paginada de resultados
        """
        results = list(self._algorithms.values())

        # Aplicar filtros
        if request.query:
            query_lower = request.query.lower()
            results = [
                a for a in results
                if query_lower in a.name.lower() or 
                   (a.description and query_lower in a.description.lower())
            ]

        if request.category:
            results = [a for a in results if a.category == request.category]

        if request.tags:
            results = [
                a for a in results
                if any(tag in a.tags for tag in request.tags)
            ]

        if request.complexity_class:
            results = [
                a for a in results
                if a.complexity_class == request.complexity_class
            ]

        if request.analyzed_only:
            results = [a for a in results if a.analyzed]

        if request.min_date:
            results = [a for a in results if a.created_at >= request.min_date]

        if request.max_date:
            results = [a for a in results if a.created_at <= request.max_date]

        # Convertir a metadata (solo campos esenciales para listados)
        metadata_list = [
            AlgorithmMetadata(
                id=a.id,
                name=a.name,
                category=a.category,
                tags=a.tags,
                complexity_class=a.complexity_class,
                big_o=a.big_o,
                created_at=a.created_at,
                analyzed=a.analyzed,
            )
            for a in results
        ]

        # Ordenar
        # (Simplificado - en producción usar sort_by y ascending)
        metadata_list.sort(key=lambda x: x.created_at, reverse=True)

        # Paginación
        total = len(metadata_list)
        # Calcular offset basado en page y page_size
        # (Asumiendo que request tiene estos campos o usar valores por defecto)
        
        return AlgorithmListResponse(
            success=True,
            message="Búsqueda completada exitosamente",
            algorithms=metadata_list,  # En producción: aplicar paginación
            total=total,
            page=1,  # Agregar paginación real
            page_size=len(metadata_list),
            total_pages=1,
        )

    # Helper Methods
    def _validate_code_size(self, code: str) -> None:
        """Valida el tamaño del código."""
        if len(code) > settings.MAX_ALGORITHM_SIZE_KB * 1024:
            raise AlgorithmTooLargeException(
                len(code),
                settings.MAX_ALGORITHM_SIZE_KB * 1024
            )

        lines = code.splitlines()
        if len(lines) > settings.MAX_ALGORITHM_LINES:
            raise ValidationException(
                f"Demasiadas líneas: {len(lines)} (máx: {settings.MAX_ALGORITHM_LINES})"
            )

    def _extract_algorithm_info(self, ast) -> AlgorithmInfo:
        """
        Extrae información del AST para crear AlgorithmInfo.

        Args:
            ast: AST parseado

        Returns:
            AlgorithmInfo: Información extraída
        """
        # Extraer parámetros
        parameters = []
        if ast.algorithm and ast.algorithm.parameters:
            for param in ast.algorithm.parameters:
                parameters.append(
                    AlgorithmParameter(
                        name=param.name,
                        type=getattr(param, 'type', None),
                        is_array=getattr(param, 'is_array', False),
                        dimensions=getattr(param, 'dimensions', []),
                        is_object=getattr(param, 'is_object', False),
                        object_type=getattr(param, 'object_type', None),
                        description=None,
                    )
                )

        # Analizar características
        has_recursion = self._detect_recursion(ast)
        has_loops = self._detect_loops(ast)
        max_nesting_depth = self._calculate_nesting_depth(ast)

        return AlgorithmInfo(
            name=ast.algorithm.name if ast.algorithm else "unknown",
            parameters=parameters,
            has_recursion=has_recursion,
            has_loops=has_loops,
            max_nesting_depth=max_nesting_depth,
            total_lines=0,  # Calcular del código
            total_statements=0,  # Calcular del AST
        )

    def _detect_recursion(self, ast) -> bool:
        """Detecta si el algoritmo tiene recursión."""
        # Simplificado - implementar lógica real
        return False

    def _detect_loops(self, ast) -> bool:
        """Detecta si el algoritmo tiene loops."""
        # Simplificado - implementar lógica real
        return True

    def _calculate_nesting_depth(self, ast) -> int:
        """Calcula la profundidad máxima de anidación."""
        # Simplificado - implementar lógica real
        return 0

    def _get_file_path(self, algorithm_id: str) -> Path:
        """Obtiene la ruta del archivo del algoritmo."""
        return self.storage_path / f"{algorithm_id}.json"

    async def _save_to_disk(self, algorithm: Algorithm) -> None:
        """Guarda el algoritmo en disco."""
        file_path = self._get_file_path(algorithm.id)
        
        # Serializar a JSON usando Pydantic
        json_data = algorithm.model_dump_json(indent=2)
        file_path.write_text(json_data, encoding='utf-8')

        logger.debug(f"Algoritmo guardado en disco: {file_path}")

    # Utility Methods
    async def increment_analysis_count(self, algorithm_id: str) -> None:
        """Incrementa el contador de análisis de un algoritmo."""
        algorithm = self._algorithms.get(algorithm_id)
        if algorithm:
            # Crear nuevo objeto con contador incrementado
            updated = Algorithm(
                **algorithm.model_dump(exclude={'analysis_count', 'analyzed'}),
                analysis_count=algorithm.analysis_count + 1,
                analyzed=True,
            )
            self._algorithms[algorithm_id] = updated
            await self._save_to_disk(updated)

    async def update_complexity(
        self,
        algorithm_id: str,
        big_o: str,
        complexity_class: AlgorithmComplexityClass
    ) -> None:
        """
        Actualiza la complejidad de un algoritmo tras análisis.

        Args:
            algorithm_id: ID del algoritmo
            big_o: Notación Big O
            complexity_class: Clase de complejidad
        """
        algorithm = self._algorithms.get(algorithm_id)
        if algorithm:
            updated = Algorithm(
                **algorithm.model_dump(exclude={'big_o', 'complexity_class'}),
                big_o=big_o,
                complexity_class=complexity_class,
            )
            self._algorithms[algorithm_id] = updated
            await self._save_to_disk(updated)

    def get_statistics(self) -> dict[str, Any]:
        """Obtiene estadísticas del servicio."""
        total = len(self._algorithms)
        
        by_category = {}
        analyzed_count = 0

        for algo in self._algorithms.values():
            # Por categoría
            cat = algo.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            # Analizados
            if algo.analyzed:
                analyzed_count += 1

        return {
            "total_algorithms": total,
            "analyzed_algorithms": analyzed_count,
            "by_category": by_category,
            "storage_path": str(self.storage_path),
        }