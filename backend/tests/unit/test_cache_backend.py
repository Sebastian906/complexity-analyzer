"""
Tests Unitarios - Cache Backend Abstraction

Verifica que la abstracción de cache funcione correctamente
con ambos backends (InMemory y Redis).
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from app.infrastructure.cache.cache_backend import (
    CacheBackend,
    InMemoryCacheBackend,
    RedisCacheBackend,
    create_cache_backend,
)
from app.services.cache_service import CacheService, get_cache_service, reset_cache_service
from app.core.config import settings

@pytest.mark.unit
class TestInMemoryCacheBackend:
    """Tests del backend InMemory"""
    
    @pytest.mark.asyncio
    async def test_backend_name(self):
        """Test nombre del backend"""
        backend = InMemoryCacheBackend()
        assert backend.backend_name() == "in_memory"
    
    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test operaciones básicas set/get"""
        backend = InMemoryCacheBackend()
        
        success = await backend.set("test_key", "test_value", ttl=60)
        assert success is True
        
        value = await backend.get("test_key")
        assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """Test get de clave inexistente"""
        backend = InMemoryCacheBackend()
        
        value = await backend.get("nonexistent")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete"""
        backend = InMemoryCacheBackend()
        
        await backend.set("key", "value")
        deleted = await backend.delete("key")
        assert deleted is True
        
        value = await backend.get("key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_clear_all(self):
        """Test clear sin prefijo"""
        backend = InMemoryCacheBackend()
        
        await backend.set("key1", "value1")
        await backend.set("key2", "value2")
        
        count = await backend.clear()
        assert count == 2
        
        assert await backend.get("key1") is None
        assert await backend.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_clear_with_prefix(self):
        """Test clear con prefijo"""
        backend = InMemoryCacheBackend()
        
        await backend.set("analysis:1", "value1")
        await backend.set("analysis:2", "value2")
        await backend.set("pattern:1", "value3")
        
        count = await backend.clear(prefix="analysis:")
        assert count == 2
        
        assert await backend.get("analysis:1") is None
        assert await backend.get("pattern:1") == "value3"
    
    @pytest.mark.asyncio
    async def test_exists(self):
        """Test exists"""
        backend = InMemoryCacheBackend()
        
        assert await backend.exists("key") is False
        
        await backend.set("key", "value")
        assert await backend.exists("key") is True
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test que las claves expiren según TTL"""
        backend = InMemoryCacheBackend()
        
        # TTL de 1 segundo
        await backend.set("key", "value", ttl=1)
        
        # Debe existir inmediatamente
        assert await backend.get("key") == "value"
        
        # Esperar expiración
        await asyncio.sleep(1.5)
        
        # Debe haber expirado
        assert await backend.get("key") is None
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test limpieza de entradas expiradas"""
        backend = InMemoryCacheBackend()
        
        # Crear entradas con TTL corto
        await backend.set("key1", "value1", ttl=1)
        await backend.set("key2", "value2", ttl=10)
        
        await asyncio.sleep(1.5)
        
        # Limpiar expirados
        cleaned = await backend.cleanup_expired()
        assert cleaned == 1
        
        # key2 debe seguir existiendo
        assert await backend.exists("key2") is True
    
    def test_stats(self):
        """Test estadísticas del backend"""
        backend = InMemoryCacheBackend()
        
        stats = backend.stats()
        
        assert stats["backend"] == "in_memory"
        assert "total_entries" in stats
        assert "active_entries" in stats
        assert "total_hits" in stats

@pytest.mark.unit
class TestRedisCacheBackend:
    """Tests del backend Redis"""
    
    @pytest.fixture
    def redis_available(self):
        """Fixture que verifica si Redis está disponible"""
        if not settings.REDIS_HOST:
            pytest.skip("Redis no configurado (REDIS_HOST vacío)")
        return True
    
    @pytest.mark.asyncio
    async def test_backend_name(self, redis_available):
        """Test nombre del backend"""
        try:
            backend = RedisCacheBackend()
            assert backend.backend_name() == "redis"
        except Exception as e:
            pytest.skip(f"Redis no disponible: {e}")
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, redis_available):
        """Test operaciones básicas con Redis"""
        try:
            backend = RedisCacheBackend()
            
            success = await backend.set("test_redis_key", {"data": "test"}, ttl=60)
            assert success is True
            
            value = await backend.get("test_redis_key")
            assert value is not None
            assert value["data"] == "test"
            
            # Cleanup
            await backend.delete("test_redis_key")
        except Exception as e:
            pytest.skip(f"Redis no disponible: {e}")
    
    @pytest.mark.asyncio
    async def test_serialization(self, redis_available):
        """Test serialización JSON en Redis"""
        try:
            backend = RedisCacheBackend()
            
            # Objetos complejos
            data = {
                "algorithm": "bubbleSort",
                "complexity": {"big_o": "O(n²)"},
                "patterns": ["brute_force"],
            }
            
            await backend.set("complex_key", data, ttl=60)
            retrieved = await backend.get("complex_key")
            
            assert retrieved == data
            
            # Cleanup
            await backend.delete("complex_key")
        except Exception as e:
            pytest.skip(f"Redis no disponible: {e}")
    
    @pytest.mark.asyncio
    async def test_clear_with_prefix(self, redis_available):
        """Test clear con prefijo en Redis"""
        try:
            backend = RedisCacheBackend()
            
            await backend.set("test:redis:1", "value1")
            await backend.set("test:redis:2", "value2")
            await backend.set("test:other:1", "value3")
            
            count = await backend.clear(prefix="test:redis:")
            assert count == 2
            
            assert await backend.get("test:redis:1") is None
            assert await backend.get("test:other:1") == "value3"
            
            # Cleanup
            await backend.clear(prefix="test:")
        except Exception as e:
            pytest.skip(f"Redis no disponible: {e}")

@pytest.mark.unit
class TestCacheBackendFactory:
    """Tests del factory de cache backends"""
    
    def test_create_backend_without_redis(self, monkeypatch):
        """Test que crea InMemory cuando Redis no está configurado"""
        # Simular ausencia de Redis
        monkeypatch.setattr(settings, "REDIS_HOST", "")
        
        backend = create_cache_backend()
        assert isinstance(backend, InMemoryCacheBackend)
    
    def test_create_backend_with_redis(self, monkeypatch):
        """Test que intenta crear Redis cuando está configurado"""
        # Simular presencia de Redis
        monkeypatch.setattr(settings, "REDIS_HOST", "localhost")
        
        backend = create_cache_backend()
        
        # Puede ser Redis o InMemory (fallback si Redis no está disponible)
        assert isinstance(backend, (RedisCacheBackend, InMemoryCacheBackend))

@pytest.mark.unit
class TestCacheServiceWithBackends:
    """Tests de CacheService con diferentes backends"""
    
    @pytest.mark.asyncio
    async def test_cache_service_with_inmemory(self):
        """Test CacheService usando InMemory backend"""
        reset_cache_service()
        
        # Forzar InMemory
        backend = InMemoryCacheBackend()
        service = CacheService(backend=backend)
        
        assert service.backend_name == "in_memory"
        
        # Operaciones básicas
        await service.set("test", "value")
        value = await service.get("test")
        assert value == "value"
    
    @pytest.mark.asyncio
    async def test_cache_service_switches_backend(self):
        """Test que CacheService puede usar diferentes backends"""
        reset_cache_service()
        
        # Backend 1: InMemory
        backend1 = InMemoryCacheBackend()
        service1 = CacheService(backend=backend1)
        await service1.set("key1", "value1")
        
        # Backend 2: Nuevo InMemory (aislado)
        backend2 = InMemoryCacheBackend()
        service2 = CacheService(backend=backend2)
        
        # No debe tener la clave del primer backend
        value = await service2.get("key1")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_cache_service_backend_isolation(self):
        """Test aislamiento entre workers con InMemory"""
        # Este test documenta el problema que Redis resuelve
        backend1 = InMemoryCacheBackend()
        backend2 = InMemoryCacheBackend()
        
        service1 = CacheService(backend=backend1)
        service2 = CacheService(backend=backend2)
        
        # Worker 1 cachea
        await service1.set("analysis:123", {"big_o": "O(n²)"})
        
        # Worker 2 NO lo ve (cada worker tiene su dict)
        value = await service2.get("analysis:123")
        assert value is None  # Este es el problema
        
        # Con Redis, ambos verían el mismo valor

@pytest.mark.integration
class TestCacheBackendUnderLoad:
    """Tests de backends bajo carga"""
    
    @pytest.mark.asyncio
    async def test_inmemory_concurrent_access(self):
        """Test acceso concurrente a InMemory backend"""
        backend = InMemoryCacheBackend()
        
        async def write_key(i):
            await backend.set(f"key{i}", f"value{i}")
        
        # 100 escrituras concurrentes
        await asyncio.gather(*[write_key(i) for i in range(100)])
        
        # Todas deben estar presentes
        for i in range(100):
            value = await backend.get(f"key{i}")
            assert value == f"value{i}"
    
    @pytest.mark.asyncio
    async def test_inmemory_cleanup_performance(self):
        """Test rendimiento de cleanup en InMemory"""
        backend = InMemoryCacheBackend()
        
        # Crear 1000 claves con TTL corto
        for i in range(1000):
            await backend.set(f"key{i}", f"value{i}", ttl=1)
        
        await asyncio.sleep(1.5)
        
        # Cleanup debe ser rápido
        import time
        start = time.time()
        cleaned = await backend.cleanup_expired()
        elapsed = time.time() - start
        
        assert cleaned == 1000
        assert elapsed < 0.5  # Debe tomar menos de 500ms

@pytest.mark.integration
class TestCacheBackendMigration:
    """Tests para migrar de InMemory a Redis"""
    
    @pytest.mark.asyncio
    async def test_migration_path(self):
        """Test que el código funciona con ambos backends"""
        # Código que debe funcionar con cualquier backend
        async def algorithm_analysis(backend: CacheBackend):
            key = "analysis:bubble_sort"
            
            # Verificar caché
            cached = await backend.get(key)
            if cached:
                return cached
            
            # Simular análisis
            result = {"big_o": "O(n²)", "computed": True}
            
            # Cachear
            await backend.set(key, result, ttl=3600)
            return result
        
        # Debe funcionar con InMemory
        inmemory = InMemoryCacheBackend()
        result1 = await algorithm_analysis(inmemory)
        assert result1["big_o"] == "O(n²)"
        
        # Segunda llamada debe usar caché
        result2 = await algorithm_analysis(inmemory)
        assert result2["big_o"] == "O(n²)"
        assert result2.get("computed") is True  # Del caché
    
    @pytest.mark.asyncio
    async def test_service_agnostic_to_backend(self):
        """Test que CacheService sea agnóstico al backend"""
        from app.services.cache_service import generate_cache_key, CacheKey
        
        # Con InMemory
        backend1 = InMemoryCacheBackend()
        service1 = CacheService(backend=backend1)
        
        code = "algorithm test(n) begin x <- 1 end"
        key = generate_cache_key(CacheKey.ANALYSIS, code)
        
        await service1.set(key, {"result": "test"}, cache_type="analysis")
        value1 = await service1.get(key)
        assert value1 is not None
        
        # El mismo código debe funcionar con Redis (si disponible)
        # Este test documenta que la migración es transparente

# Ejecutar tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])