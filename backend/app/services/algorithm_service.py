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

from app.profiling import get_performance_monitor

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

        # PROFILING INIT 
        self.profiling_enabled = settings.APP_ENV in ["development", "staging"]
        if self.profiling_enabled:
            self.monitor = get_performance_monitor()
        else:
            self.monitor = None
        
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

        # PROFILING: Creación de algoritmo
        if self.profiling_enabled and self.monitor:
            with self.monitor.monitor("algorithm_create", module="algorithm_service"):
                return await self._create_impl(request)
        else:
            return await self._create_impl(request)

    async def _create_impl(self, request: AlgorithmCreate) -> AlgorithmResponse:
        """Implementación interna de create."""
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
        # PROFILING: Lectura de algoritmo
        if self.profiling_enabled and self.monitor:
            with self.monitor.monitor("algorithm_get", module="algorithm_service"):
                return await self._get_impl(algorithm_id)
        else:
            return await self._get_impl(algorithm_id)
        
    async def _get_impl(self, algorithm_id: str) -> Optional[AlgorithmResponse]:
        """Implementación interna de get."""
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
        # PROFILING: Actualización de algoritmo
        if self.profiling_enabled and self.monitor:
            with self.monitor.monitor("algorithm_update", module="algorithm_service"):
                return await self._update_impl(algorithm_id, request)
        else:
            return await self._update_impl(algorithm_id, request)

    async def _update_impl(
        self,
        algorithm_id: str,
        request: AlgorithmUpdate
    ) -> Optional[AlgorithmResponse]:
        """Implementación interna de update."""
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

        # Manejar campos opcionales con getattr()
        # Los campos en AlgorithmUpdate son Optional, pueden ser None

        # Helper para obtener valor o usar existing
        def get_updated_value(field_name, default=None):
            """Obtiene valor actualizado o mantiene el existente"""
            new_val = getattr(request, field_name, None)
            if new_val is not None:
                return new_val
            return getattr(existing, field_name, default)

        updated_algorithm = Algorithm(
            id=existing.id,
            name=get_updated_value('name'),
            description=get_updated_value('description'),
            category=get_updated_value('category'),
            tags=get_updated_value('tags', []),
            language=get_updated_value('language', 'pseudocode'),
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
        # ========== PROFILING: Eliminación de algoritmo ==========
        if self.profiling_enabled and self.monitor:
            with self.monitor.monitor("algorithm_delete", module="algorithm_service"):
                return await self._delete_impl(algorithm_id)
        else:
            return await self._delete_impl(algorithm_id)

    async def _delete_impl(self, algorithm_id: str) -> bool:
        """Implementación interna de delete."""
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
        # PROFILING: Búsqueda de algoritmos
        if self.profiling_enabled and self.monitor:
            with self.monitor.monitor("algorithm_search", module="algorithm_service"):
                return await self._search_impl(request)
        else:
            return await self._search_impl(request)
        
    async def _search_impl(
        self,
        request: AlgorithmSearchCriteria
    ) -> AlgorithmListResponse:
        """Implementación interna de search."""
        logger.info(f"Buscando algoritmos con criterios: {request}")
    
        # Construir filtro
        filter_dict = {}

        if request.category:
            filter_dict["category"] = request.category.value

        if request.tags:
            filter_dict["tags"] = {"$all": request.tags}    

        if request.complexity_class:
            filter_dict["complexity_class"] = request.complexity_class.value

        # Si se pidió solo algoritmos ya analizados
        if getattr(request, "analyzed_only", False):
            filter_dict["analyzed"] = True
        # Ejecutar búsqueda sobre el índice en memoria
        try:
            all_algos = list(self._algorithms.values())

            # Aplicar filtros
            def matches(algo: Algorithm) -> bool:
                # category
                if request.category:
                    req_cat = getattr(request, 'category')
                    # comparar por value si es Enum
                    if hasattr(req_cat, 'value'):
                        if algo.category.value != req_cat.value:
                            return False
                    else:
                        if algo.category.value != str(req_cat):
                            return False

                # tags (todos deben estar presentes)
                if request.tags:
                    req_tags = [t.lower() for t in request.tags]
                    algo_tags = [t.lower() for t in (algo.tags or [])]
                    for t in req_tags:
                        if t not in algo_tags:
                            return False

                # complexity_class
                if request.complexity_class:
                    req_cc = getattr(request, 'complexity_class')
                    if hasattr(req_cc, 'value'):
                        if (algo.complexity_class or '') != req_cc.value:
                            return False
                    else:
                        if (algo.complexity_class or '') != str(req_cc):
                            return False

                # analyzed_only
                if getattr(request, 'analyzed_only', False):
                    if not getattr(algo, 'analyzed', False):
                        return False

                # free text query
                if request.query:
                    q = request.query.lower()
                    if q not in (algo.name or '').lower() and q not in (algo.description or '').lower():
                        # también buscar en tags
                        if not any(q in t.lower() for t in (algo.tags or [])):
                            return False

                # date filters
                if getattr(request, 'min_date', None):
                    if algo.created_at < request.min_date:
                        return False
                if getattr(request, 'max_date', None):
                    if algo.created_at > request.max_date:
                        return False

                return True

            filtered = [a for a in all_algos if matches(a)]

            # Convertir a AlgorithmMetadata
            metadata_list = [
                AlgorithmMetadata(
                    id=a.id,
                    name=a.name,
                    category=a.category,
                    tags=a.tags or [],
                    complexity_class=a.complexity_class,
                    big_o=a.big_o,
                    created_at=a.created_at,
                    analyzed=bool(a.analyzed),
                )
                for a in filtered
            ]

            total = len(metadata_list)

            # Paginación: usar atributos opcionales 'limit' y 'offset' si vienen en el request
            page_size = max(getattr(request, 'limit', None) or 10, 1)
            offset = max(getattr(request, 'offset', None) or 0, 0)
            page = max(offset // page_size + 1, 1)
            total_pages = max((total + page_size - 1) // page_size, 1)

            # Slice
            start = offset
            end = offset + page_size
            paged = metadata_list[start:end]

            return AlgorithmListResponse(
                success=True,
                message="Búsqueda completada exitosamente",
                timestamp=None,
                algorithms=paged,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            raise

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