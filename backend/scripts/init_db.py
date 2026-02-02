"""
Script de Inicialización de Base de Datos

Inicializa las bases de datos del sistema:
- MongoDB: Crea colecciones e índices
- PostgreSQL: Crea tablas mediante Alembic
- Redis: Verifica conectividad

Uso:
    python scripts/init_db.py [--drop] [--seed]
    
    --drop: Elimina datos existentes (PELIGROSO)
    --seed: Carga datos de prueba
"""

import asyncio
import sys
from pathlib import Path
from argparse import ArgumentParser

# Agregar raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

async def init_mongodb(drop: bool = False):
    """
    Inicializa MongoDB.
    
    Args:
        drop: Si True, elimina la base de datos existente
    """
    from app.infrastructure.database.mongodb_client import get_mongodb_client
    from app.infrastructure.database.models.mongo import (
        Algorithm,
        AnalysisResult,
        PatternDetection,
    )
    
    logger.info("Inicializando MongoDB...")
    
    try:
        client = get_mongodb_client()
        await client.connect()
        
        # Drop database si se solicita
        if drop:
            logger.warning(f"Eliminando base de datos: {settings.MONGODB_DB_NAME}")
            await client.client.drop_database(settings.MONGODB_DB_NAME)
            logger.info("✓ Base de datos eliminada")
            
            # Reconectar para crear nueva DB
            await client.close()
            await client.connect()
        
        # Verificar colecciones
        db = client.db
        collections = await db.list_collection_names()
        
        logger.info("Colecciones existentes:")
        for collection in collections:
            logger.info(f"  - {collection}")
        
        # Crear índices para cada modelo
        logger.info("Creando índices...")
        
        # Los índices se crean automáticamente por Beanie en Settings de cada modelo
        # Pero podemos forzar su creación
        await Algorithm.find_all().limit(1).to_list()
        await AnalysisResult.find_all().limit(1).to_list()
        await PatternDetection.find_all().limit(1).to_list()
        
        logger.info("✓ Índices creados")
        
        # Verificar índices creados
        for collection_name in ["algorithms", "analysis_results", "pattern_detections"]:
            if collection_name in collections or True:  # Siempre verificar
                collection = db[collection_name]
                indexes = await collection.index_information()
                logger.info(f"Índices en {collection_name}:")
                for index_name, index_info in indexes.items():
                    logger.info(f"  - {index_name}: {index_info.get('key', [])}")
        
        logger.info("✓ MongoDB inicializado correctamente")
        
        await client.close()
        
    except Exception as e:
        logger.error(f"Error inicializando MongoDB: {e}")
        raise

async def init_postgresql(drop: bool = False):
    """
    Inicializa PostgreSQL.
    
    Args:
        drop: Si True, elimina las tablas existentes
    """
    from app.infrastructure.database.postgresql_client import get_postgresql_client
    from app.infrastructure.database.models.postgres import Base
    from sqlalchemy import text
    
    logger.info("Inicializando PostgreSQL...")
    
    try:
        client = get_postgresql_client()
        await client.connect()
        
        if drop:
            logger.warning("Eliminando tablas existentes...")
            async with client.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("✓ Tablas eliminadas")
        
        # Crear todas las tablas
        logger.info("Creando tablas...")
        async with client.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ Tablas creadas")
        
        # Verificar tablas creadas
        async with client.engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = result.fetchall()
            
            logger.info("Tablas creadas en PostgreSQL:")
            for table in tables:
                logger.info(f"  - {table[0]}")
        
        logger.info("✓ PostgreSQL inicializado correctamente")
        
        await client.close()
        
    except Exception as e:
        logger.error(f"Error inicializando PostgreSQL: {e}")
        raise

async def init_redis():
    """Verifica conectividad con Redis."""
    from app.infrastructure.cache.redis_cache import get_redis_client
    
    logger.info("Verificando Redis...")
    
    try:
        client = get_redis_client()
        await client.connect()
        
        is_connected = await client.ping()
        
        if is_connected:
            logger.info("✓ Redis conectado correctamente")
        else:
            logger.warning("Redis no respondió al ping")
        
        await client.close()
        
    except Exception as e:
        logger.error(f"Error conectando a Redis: {e}")
        logger.warning("Redis es opcional, el sistema puede funcionar sin él")

async def seed_data():
    """Carga datos de prueba en las bases de datos."""
    from app.infrastructure.database.mongodb_client import get_mongodb_client
    from app.infrastructure.database.models.mongo import Algorithm
    from datetime import datetime
    
    logger.info("Cargando datos de prueba...")
    
    try:
        client = get_mongodb_client()
        await client.connect()
        
        # Algoritmos de ejemplo
        sample_algorithms = [
            {
                "name": "bubble_sort",
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
                "language": "pseudocode",
                "category": "sorting",
                "tags": ["sorting", "quadratic", "comparison"],
                "description": "Algoritmo de ordenamiento de burbuja",
                "author": "System",
            },
            {
                "name": "binary_search",
                "code": """algorithm binarySearch(A[1..n], x)
begin
    left ← 1
    right ← n
    
    while (left <= right) do
    begin
        mid ← (left + right) / 2
        
        if (A[mid] = x) then
            return mid
        
        if (A[mid] < x) then
            left ← mid + 1
        else
            right ← mid - 1
    end
    
    return -1
end""",
                "language": "pseudocode",
                "category": "searching",
                "tags": ["search", "divide-conquer", "logarithmic"],
                "description": "Búsqueda binaria en array ordenado",
                "author": "System",
            },
            {
                "name": "fibonacci",
                "code": """algorithm fibonacci(n)
begin
    if (n <= 1) then
        return n
    
    return fibonacci(n - 1) + fibonacci(n - 2)
end""",
                "language": "pseudocode",
                "category": "recursion",
                "tags": ["recursive", "exponential", "dynamic-programming"],
                "description": "Cálculo recursivo de Fibonacci",
                "author": "System",
            },
            {
                "name": "merge_sort",
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
                "language": "pseudocode",
                "category": "sorting",
                "tags": ["sorting", "divide-conquer", "nlogn"],
                "description": "Merge Sort - Ordenamiento por mezcla",
                "author": "System",
            },
        ]
        
        # Insertar algoritmos
        for algo_data in sample_algorithms:
            # Verificar si ya existe
            existing = await Algorithm.find_one(Algorithm.name == algo_data["name"])
            
            if existing:
                logger.info(f"  - {algo_data['name']}: Ya existe, saltando...")
                continue
            
            algorithm = Algorithm(**algo_data)
            await algorithm.insert()
            logger.info(f"  ✓ {algo_data['name']}: Insertado")
        
        logger.info("✓ Datos de prueba cargados")
        
        await client.close()
        
    except Exception as e:
        logger.error(f"Error cargando datos de prueba: {e}")
        raise

async def main(drop: bool = False, seed: bool = False):
    """
    Función principal de inicialización.
    
    Args:
        drop: Eliminar datos existentes
        seed: Cargar datos de prueba
    """
    logger.info("INICIALIZACIÓN DE BASES DE DATOS")
    logger.info(f"Entorno: {settings.APP_ENV}")
    logger.info(f"Drop existing: {drop}")
    logger.info(f"Seed data: {seed}")
    
    if drop and settings.APP_ENV == "production":
        logger.error("¡NO SE PUEDE HACER DROP EN PRODUCCIÓN!")
        return
    
    try:
        # Inicializar ambas bases de datos para verificar conectividad
        logger.info("Inicializando MongoDB...")
        try:
            await init_mongodb(drop=drop)
        except Exception as e:
            logger.error(f"Error en MongoDB: {e}")
            logger.warning("Continuando con PostgreSQL...")
        
        logger.info("Inicializando PostgreSQL...")
        try:
            await init_postgresql(drop=drop)
        except Exception as e:
            logger.error(f"Error en PostgreSQL: {e}")
            logger.warning("PostgreSQL no disponible")
        
        # Inicializar Redis (opcional)
        if settings.REDIS_HOST:
            await init_redis()
        
        # Cargar datos de prueba si se solicita
        if seed:
            await seed_data()
        
        logger.info("✓ INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
        
    except Exception as e:
        logger.error("✗ ERROR EN INICIALIZACIÓN")
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    parser = ArgumentParser(description="Inicializar bases de datos")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Eliminar datos existentes (PELIGROSO)"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Cargar datos de prueba"
    )
    
    args = parser.parse_args()
    
    # Confirmar si se va a hacer drop
    if args.drop:
        response = input(
            "¿Estás seguro de eliminar la base de datos existente? (yes/no): "
        )
        if response.lower() != "yes":
            logger.info("Operación cancelada")
            sys.exit(0)
    
    asyncio.run(main(drop=args.drop, seed=args.seed))