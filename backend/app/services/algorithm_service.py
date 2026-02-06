"""
Algorithm Service - Servicio de Gestión de Algoritmos

Proporciona operaciones CRUD y gestión completa de algoritmos,
incluyendo almacenamiento, búsqueda y versionado.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Any
from urllib import request
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

from app.infrastructure.database.repositories import AlgorithmRepository
from app.infrastructure.database.models.mongo import Algorithm as AlgorithmModel

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
        parser: Optional[PseudocodeParser] = None,
        repository: Optional[AlgorithmRepository] = None
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
        self.repository = repository or AlgorithmRepository()
        self._initialized = False

        # Índice en memoria (migrar a MongoDB en producción)
        self._algorithms: dict[str, Algorithm] = {}

        # PROFILING INIT 
        self.profiling_enabled = settings.APP_ENV in ["development", "staging"]
        if self.profiling_enabled:
            self.monitor = get_performance_monitor()
        else:
            self.monitor = None
        
        logger.info(f"AlgorithmService inicializado - Storage: {self.storage_path}")

    async def initialize(self):
        """
        Inicializa la conexión a MongoDB.
        
        Debe llamarse después de crear la instancia.
        """
        if self._initialized:
            return
            
        if self.repository is None:
            from app.infrastructure.database import get_mongodb_client
            
            # Conectar a MongoDB si no está conectado
            mongo_client = get_mongodb_client()
            if not mongo_client.is_connected:
                await mongo_client.connect()
            
            # Crear repository
            self.repository = AlgorithmRepository()
        
        self._initialized = True
        logger.info("AlgorithmService conectado a MongoDB")

    # Validation
    async def validate_code(self, code: str) -> bool:
        """
        Valida que el código sea sintácticamente correcto.
        
        Args:
            code: Código a validar
            
        Returns:
            True si el código es válido
            
        Raises:
            ValidationException: Si el código no es válido
        """
        # Validar tamaño
        self._validate_code_size(code)
        
        # Validar sintaxis parseando el código
        try:
            self.parser.parse(code, validate=True)
            return True
        except Exception as e:
            logger.error(f"Error validando código: {e}")
            raise ValidationException(f"Código inválido: {e}")

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

        # No forzamos un id para MongoDB: dejamos que Beanie genere el ObjectId
        # Generar timestamps
        now = datetime.utcnow()

        # Crear modelo para MongoDB (sin id para que Mongo genere ObjectId)
        algorithm_model = AlgorithmModel(
            name=request.name,
            description=request.description,
            category=request.category.value if request.category else None,
            tags=request.tags or [],
            language=request.language.value if hasattr(request.language, 'value') else (request.language or "pseudocode"),
            code=request.code,
            created_at=now,
            updated_at=now,
        )

        # Guardar en MongoDB (si hay repository)
        if self.repository:
            created_model = await self.repository.create(algorithm_model)
            # Obtener id asignado por Mongo como string
            algorithm_id = str(created_model.id)
            logger.info(f"Algoritmo guardado en MongoDB: {algorithm_id}")
            # Usar timestamps devueltos por el modelo creado si existen
            created_at = getattr(created_model, 'created_at', now)
            updated_at = getattr(created_model, 'updated_at', now)
        else:
            # Fallback: usar un UUID local si no hay repository
            algorithm_id = str(uuid4())
            created_model = algorithm_model
            created_at = now
            updated_at = now
            logger.warning("Repository no disponible, solo guardado local")

        # Crear objeto Algorithm (schema de respuesta) usando id como string
        algorithm = Algorithm(
            id=algorithm_id,
            name=request.name,
            description=request.description,
            category=request.category,
            tags=request.tags,
            language=request.language,
            code=request.code,
            info=algorithm_info,
            created_at=created_at,
            updated_at=updated_at,
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
        # Intentar primero desde MongoDB
        if self.repository:
            algorithm_model = await self.repository.get_by_id(algorithm_id)
            
            if algorithm_model:
                # Convertir modelo MongoDB a schema
                algorithm = self._model_to_schema(algorithm_model)
                
                # Actualizar caché
                self._algorithms[algorithm_id] = algorithm
                
                return AlgorithmResponse(
                    success=True,
                    message="Algoritmo recuperado exitosamente",
                    algorithm=algorithm
                )
        
        # Fallback: buscar en caché local
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

        # Eliminar de MongoDB
        if self.repository:
            success = await self.repository.delete(algorithm_id)
            if success:
                logger.info(f"Algoritmo eliminado de MongoDB: {algorithm_id}")
            else:
                logger.warning(f"Algoritmo no encontrado en MongoDB: {algorithm_id}")
        
        # Eliminar del disco y caché
        if algorithm_id in self._algorithms:
            del self._algorithms[algorithm_id]
        
        file_path = self._get_file_path(algorithm_id)
        if file_path.exists():
            file_path.unlink()

        logger.info(f"Algoritmo eliminado: {algorithm_id}")
        return True

    async def search(
        self,
        request: AlgorithmSearchCriteria,
        page: int = 1,
        page_size: int = 10
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
                return await self._search_impl(request, page=page, page_size=page_size)
        else:
            return await self._search_impl(request, page=page, page_size=page_size)
        
    async def _search_impl(
        self,
        request: AlgorithmSearchCriteria,
        page: int = 1,
        page_size: int = 10
    ) -> AlgorithmListResponse:
        """Implementación interna de search."""
        logger.info(f"Buscando algoritmos con criterios: {request}")

        # BÚSQUEDA EN MONGODB
        if self.repository:
            try:
                # Construir filtro MongoDB
                filter_dict = {}

                if request.category:
                    filter_dict["category"] = request.category.value

                if request.tags:
                    # Usar $in para que coincida si tiene alguno de los tags
                    filter_dict["tags"] = {"$in": request.tags}

                if request.complexity_class:
                    filter_dict["complexity_class"] = request.complexity_class.value

                if request.analyzed_only:
                    filter_dict["analyzed"] = True

                # Filtros de fecha
                if request.min_date or request.max_date:
                    date_filter = {}
                    if request.min_date:
                        date_filter["$gte"] = request.min_date
                    if request.max_date:
                        date_filter["$lte"] = request.max_date
                    filter_dict["created_at"] = date_filter

                # Búsqueda de texto libre (si existe)
                if request.query:
                    # MongoDB text search (requiere índice de texto)
                    # Alternativa: usar regex
                    filter_dict["$or"] = [
                        {"name": {"$regex": request.query, "$options": "i"}},
                        {"description": {"$regex": request.query, "$options": "i"}}
                    ]

                logger.debug(f"Filtro MongoDB: {filter_dict}")

                # Calcular skip para paginación
                skip = (page - 1) * page_size

                # Buscar en MongoDB con paginación
                algorithms_models = await self.repository.find(
                    filter_dict,
                    skip=skip,
                    limit=page_size
                )

                # Contar total de documentos que coinciden
                total = await self.repository.count(filter_dict)

                logger.info(f"Encontrados {total} algoritmos en MongoDB, mostrando {len(algorithms_models)}")

                # Convertir modelos a metadata
                metadata_list = []
                for model in algorithms_models:
                    try:
                        # Protección contra tipos inesperados
                        if isinstance(model, tuple):
                            logger.warning(f"Modelo es tupla, intentando extraer primer elemento")
                            model = model[0] if len(model) > 0 else None
                            if model is None:
                                continue
                        
                        # Obtener id de manera segura (puede ser PydanticObjectId o str)
                        model_id = str(getattr(model, 'id', None) or getattr(model, '_id', ''))
                        
                        metadata = AlgorithmMetadata(
                            id=model_id,
                            name=getattr(model, 'name', 'Unknown'),
                            category=AlgorithmCategory(model.category) if getattr(model, 'category', None) else AlgorithmCategory.OTHER,
                            tags=getattr(model, 'tags', None) or [],
                            complexity_class=AlgorithmComplexityClass(model.complexity_class) if getattr(model, 'complexity_class', None) else None,
                            big_o=getattr(model, 'big_o', None),
                            created_at=getattr(model, 'created_at', datetime.utcnow()),
                            analyzed=getattr(model, 'analyzed', False),
                        )
                        metadata_list.append(metadata)
                    except Exception as e:
                        logger.error(f"Error convirtiendo modelo: {e}")
                        continue
                    
                # Calcular páginas totales
                total_pages = max((total + page_size - 1) // page_size, 1) if total > 0 else 1

                return AlgorithmListResponse(
                    success=True,
                    message="Búsqueda completada exitosamente",
                    algorithms=metadata_list,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                )

            except Exception as e:
                logger.error(f"Error en búsqueda MongoDB: {e}", exc_info=True)
                # Continuar con fallback a memoria

        # ========== FALLBACK: BÚSQUEDA EN MEMORIA ==========
        logger.warning("Usando búsqueda en memoria (fallback)")

        all_algos = list(self._algorithms.values())

        # Aplicar filtros en memoria
        def matches(algo: Algorithm) -> bool:
            # category
            if request.category:
                if algo.category != request.category:
                    return False

            # tags (si tiene ALGUNO de los tags solicitados)
            if request.tags:
                algo_tags_lower = [t.lower() for t in (algo.tags or [])]
                req_tags_lower = [t.lower() for t in request.tags]
                if not any(t in algo_tags_lower for t in req_tags_lower):
                    return False

            # complexity_class
            if request.complexity_class:
                if algo.complexity_class != request.complexity_class:
                    return False

            # analyzed_only
            if request.analyzed_only:
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
            if request.min_date:
                if algo.created_at < request.min_date:
                    return False
            if request.max_date:
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

        # Paginación
        skip = (page - 1) * page_size
        paged = metadata_list[skip:skip + page_size]

        total_pages = max((total + page_size - 1) // page_size, 1) if total > 0 else 1

        return AlgorithmListResponse(
            success=True,
            message="Búsqueda completada exitosamente",
            algorithms=paged,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
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
    
    def _model_to_schema(self, model: AlgorithmModel) -> Algorithm:
        """Convierte AlgorithmModel MongoDB a Algorithm schema."""
        # Reconstruir AlgorithmInfo
        info = AlgorithmInfo(
            name=model.name,
            parameters=[],
            has_recursion=False,
            has_loops=False,
            max_nesting_depth=0,
            total_lines=len(model.code.splitlines()),
            total_statements=0,
        )

        return Algorithm(
            id=str(model.id),
            name=model.name,
            description=model.description,
            category=AlgorithmCategory(model.category) if model.category else AlgorithmCategory.OTHER,
            tags=model.tags or [],
            language=model.language or "pseudocode",
            code=model.code,
            info=info,
            created_at=model.created_at,
            updated_at=model.updated_at,
            analyzed=getattr(model, 'analyzed', False),
            analysis_count=getattr(model, 'analysis_count', 0),
            complexity_class=AlgorithmComplexityClass(model.complexity_class) if getattr(model, 'complexity_class', None) else None,
            big_o=getattr(model, 'big_o', None),
        )

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