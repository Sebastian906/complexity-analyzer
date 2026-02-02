"""
Tests de Integración - Operaciones de Caché

Prueba operaciones de caché con Redis.
"""

import pytest
import asyncio
from datetime import datetime

from app.infrastructure.cache import (
    get_redis_client,
    CachePrefix,
    CacheTTL,
    build_analysis_key,
    build_pattern_key,
    build_llm_key,
    hash_content,
)
from app.infrastructure.database import CacheRepository
from app.core.config import settings

@pytest.mark.integration
class TestRedisOperations:
    """Tests de operaciones básicas con Redis"""
    
    @pytest.mark.skipif(
        not settings.REDIS_HOST,
        reason="Redis not configured"
    )
    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """Test conexión a Redis"""
        client = get_redis_client()
        await client.connect()
        
        is_connected = await client.ping()
        assert is_connected is True
        
        await client.close()
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_redis_set_get(self):
        """Test set y get básicos"""
        client = get_redis_client()
        await client.connect()
        
        key = "test:integration:set_get"
        value = {"message": "Hello Redis", "timestamp": datetime.utcnow().isoformat()}
        
        # Set
        success = await client.set(key, value, ttl=60)
        assert success is True
        
        # Get
        retrieved = await client.get(key)
        assert retrieved is not None
        assert retrieved["message"] == "Hello Redis"
        
        # Limpiar
        await client.delete(key)
        
        await client.close()
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_redis_delete(self):
        """Test eliminación de clave"""
        client = get_redis_client()
        await client.connect()
        
        key = "test:integration:delete"
        value = {"data": "to be deleted"}
        
        # Set
        await client.set(key, value, ttl=60)
        
        # Verificar que existe
        retrieved = await client.get(key)
        assert retrieved is not None
        
        # Delete
        deleted = await client.delete(key)
        assert deleted is True
        
        # Verificar que no existe
        retrieved = await client.get(key)
        assert retrieved is None
        
        await client.close()
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_redis_ttl_expiration(self):
        """Test expiración de TTL"""
        client = get_redis_client()
        await client.connect()
        
        key = "test:integration:ttl"
        value = {"data": "expires soon"}
        
        # Set con TTL de 2 segundos
        await client.set(key, value, ttl=2)
        
        # Verificar que existe inmediatamente
        retrieved = await client.get(key)
        assert retrieved is not None
        
        # Esperar a que expire
        await asyncio.sleep(3)
        
        # Verificar que expiró
        retrieved = await client.get(key)
        assert retrieved is None
        
        await client.close()

@pytest.mark.integration
class TestCacheRepository:
    """Tests del CacheRepository"""
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_cache_repository_get_set(self):
        """Test get y set del repositorio"""
        repo = CacheRepository()
        
        key = "test:repo:get_set"
        value = {"test": "data", "number": 42}
        
        # Set
        success = await repo.set(key, value, ttl=60)
        assert success is True
        
        # Get
        retrieved = await repo.get(key)
        assert retrieved is not None
        assert retrieved["test"] == "data"
        assert retrieved["number"] == 42
        
        # Limpiar
        await repo.delete(key)
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_cache_repository_exists(self):
        """Test verificar existencia de clave"""
        repo = CacheRepository()
        
        key = "test:repo:exists"
        value = {"data": "test"}
        
        # No debe existir inicialmente
        exists = await repo.exists(key)
        assert exists is False
        
        # Crear
        await repo.set(key, value, ttl=60)
        
        # Ahora debe existir
        exists = await repo.exists(key)
        assert exists is True
        
        # Limpiar
        await repo.delete(key)
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_cache_analysis_result(self):
        """Test cachear resultado de análisis"""
        repo = CacheRepository()
        
        algorithm_id = "test_algo_123"
        analysis_result = {
            "big_o": "O(n)",
            "omega": "Ω(n)",
            "theta": "Θ(n)",
            "analysis_time": 0.123,
        }
        
        # Cachear
        success = await repo.cache_analysis_result(algorithm_id, analysis_result)
        assert success is True
        
        # Recuperar
        retrieved = await repo.get_cached_analysis(algorithm_id)
        assert retrieved is not None
        assert retrieved["big_o"] == "O(n)"
        assert retrieved["omega"] == "Ω(n)"
        
        # Limpiar
        await repo.invalidate_analysis_cache(algorithm_id)
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_cache_pattern_detection(self):
        """Test cachear detección de patrones"""
        repo = CacheRepository()
        
        algorithm_id = "test_algo_patterns"
        patterns = {
            "primary_pattern": "divide_and_conquer",
            "primary_confidence": 0.85,
            "patterns_found": [
                {"name": "divide_and_conquer", "confidence": 0.85},
                {"name": "recursion", "confidence": 0.75},
            ],
        }
        
        # Cachear
        success = await repo.cache_pattern_detection(algorithm_id, patterns)
        assert success is True
        
        # Recuperar
        retrieved = await repo.get_cached_patterns(algorithm_id)
        assert retrieved is not None
        assert retrieved["primary_pattern"] == "divide_and_conquer"
        assert retrieved["primary_confidence"] == 0.85
        
        # Limpiar
        key = build_pattern_key(algorithm_id)
        await repo.delete(key)
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_cache_llm_response(self):
        """Test cachear respuesta de LLM"""
        repo = CacheRepository()
        
        prompt = "Analiza este algoritmo: bubble sort"
        prompt_hash = hash_content(prompt)
        llm_type = "claude"
        
        response = {
            "big_o": "O(n²)",
            "omega": "Ω(n²)",
            "reasoning": "Dos loops anidados",
        }
        
        # Cachear
        success = await repo.cache_llm_response(prompt_hash, llm_type, response)
        assert success is True
        
        # Recuperar
        retrieved = await repo.get_cached_llm_response(prompt_hash, llm_type)
        assert retrieved is not None
        assert retrieved["big_o"] == "O(n²)"
        assert retrieved["reasoning"] == "Dos loops anidados"
        
        # Limpiar
        key = build_llm_key(prompt, llm_type)
        await repo.delete(key)
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_cache_get_many(self):
        """Test obtener múltiples valores"""
        repo = CacheRepository()
        
        # Crear múltiples entradas
        keys = []
        for i in range(3):
            key = f"test:repo:many:{i}"
            value = {"index": i, "data": f"value_{i}"}
            await repo.set(key, value, ttl=60)
            keys.append(key)
        
        # Obtener múltiples
        results = await repo.get_many(keys)
        
        assert len(results) == 3
        for i, key in enumerate(keys):
            assert key in results
            assert results[key]["index"] == i
        
        # Limpiar
        await repo.delete_many(keys)
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_cache_set_many(self):
        """Test guardar múltiples valores"""
        repo = CacheRepository()
        
        # Preparar datos
        items = {}
        keys = []
        for i in range(3):
            key = f"test:repo:set_many:{i}"
            value = {"index": i, "data": f"batch_value_{i}"}
            items[key] = value
            keys.append(key)
        
        # Guardar múltiples
        count = await repo.set_many(items, ttl=60)
        assert count == 3
        
        # Verificar que se guardaron
        for key in keys:
            retrieved = await repo.get(key)
            assert retrieved is not None
        
        # Limpiar
        await repo.delete_many(keys)
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test obtener estadísticas de caché"""
        repo = CacheRepository()
        
        stats = await repo.get_cache_stats()
        
        assert "connected" in stats
        assert stats["connected"] is True
        assert stats["type"] == "redis"

@pytest.mark.integration
class TestCacheKeys:
    """Tests de construcción de claves de caché"""
    
    def test_build_analysis_key(self):
        """Test construcción de clave de análisis"""
        key = build_analysis_key("algo_123")
        
        assert key == "analysis:algo_123"
        assert key.startswith(CachePrefix.ANALYSIS)
    
    def test_build_pattern_key(self):
        """Test construcción de clave de patrón"""
        key = build_pattern_key("algo_456")
        
        assert key == "pattern:algo_456"
        assert key.startswith(CachePrefix.PATTERN)
    
    def test_build_llm_key(self):
        """Test construcción de clave de LLM"""
        prompt = "Test prompt for caching"
        llm_type = "claude"
        
        key = build_llm_key(prompt, llm_type)
        
        assert key.startswith(f"{CachePrefix.LLM}:{llm_type}")
        assert len(key.split(":")) == 3  # llm:claude:hash
    
    def test_hash_content(self):
        """Test hash de contenido"""
        content1 = "Test content"
        content2 = "Test content"
        content3 = "Different content"
        
        hash1 = hash_content(content1)
        hash2 = hash_content(content2)
        hash3 = hash_content(content3)
        
        # Mismo contenido debe dar mismo hash
        assert hash1 == hash2
        
        # Diferente contenido debe dar diferente hash
        assert hash1 != hash3
        
        # Hash debe tener longitud 16 (por defecto)
        assert len(hash1) == 16

@pytest.mark.integration
class TestCacheIntegrationWithServices:
    """Tests de integración de caché con servicios"""
    
    @pytest.mark.skipif(not settings.REDIS_HOST, reason="Redis not configured")
    @pytest.mark.asyncio
    async def test_cache_in_analysis_workflow(self):
        """Test uso de caché en flujo de análisis"""
        from app.services import get_cache_service
        from app.services.cache_service import generate_cache_key, CacheKey
        
        cache_service = get_cache_service()
        
        algorithm_id = "test_workflow_123"
        analysis_data = {
            "algorithm_name": "test_algorithm",
            "big_o": "O(n log n)",
            "omega": "Ω(n log n)",
            "theta": "Θ(n log n)",
        }
        
        # Generar clave de caché
        cache_key = generate_cache_key(CacheKey.ANALYSIS, algorithm_id)
        
        # Primera vez - no debe estar en caché
        cached = await cache_service.get(cache_key)
        assert cached is None
        
        # Cachear
        await cache_service.set(cache_key, analysis_data)
        
        # Segunda vez - debe estar en caché
        cached = await cache_service.get(cache_key)
        assert cached is not None
        assert cached["big_o"] == "O(n log n)"
        
        # Limpiar
        await cache_service.delete(cache_key)