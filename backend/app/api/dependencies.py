"""
Dependency Injection

Dependencias compartidas para los endpoints de FastAPI.
"""

from typing import Generator

from fastapi import Depends, HTTPException, Header, status

from app.core.config import settings
from app.core.parser import PseudocodeParser


# Parser Dependency

def get_parser() -> PseudocodeParser:
    """
    Dependency para obtener instancia del parser.
    
    Returns:
        PseudocodeParser: Instancia del parser
    
    Example:
        ```python
        @router.post("/parse")
        async def parse(
            code: str,
            parser: PseudocodeParser = Depends(get_parser)
        ):
            ast = parser.parse(code)
            return ast
        ```
    """
    return PseudocodeParser()


# API Key Dependency (opcional, para proteger endpoints)

async def verify_api_key(
    x_api_key: str = Header(..., alias=settings.API_KEY_HEADER)
) -> str:
    """
    Dependency para verificar API key.
    
    Args:
        x_api_key: API key del header
    
    Returns:
        str: API key verificada
    
    Raises:
        HTTPException 401: API key inválida
    """
    # En producción, verificar contra base de datos
    # Por ahora, comparación simple
    if settings.SECRET_KEY and x_api_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida"
        )
    
    return x_api_key


# Rate Limiting Dependency (placeholder)

class RateLimiter:
    """Rate limiter simple (placeholder para implementación completa)"""
    
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self._request_counts: dict = {}  # In-memory fallback
    
    async def __call__(self) -> None:
        """Verifica rate limit usando Redis o fallback en memoria"""
        import time
        from fastapi import HTTPException
        
        # Intentar usar Redis si está disponible
        try:
            from app.infrastructure.cache.redis_cache import get_redis_client
            client = get_redis_client()
            
            if client.client:
                # Usar Redis para rate limiting distribuido
                key = f"rate_limit:{id(self)}:{int(time.time() // self.period)}"
                current = await client.client.incr(key)
                
                if current == 1:
                    await client.client.expire(key, self.period)
                
                if current > self.calls:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit excedido: {self.calls} llamadas por {self.period}s"
                    )
                return
        except ImportError:
            pass
        except Exception:
            pass  # Fallback a in-memory
        
        # Fallback: rate limiting en memoria (single instance)
        current_window = int(time.time() // self.period)
        key = f"{id(self)}:{current_window}"
        
        # Limpiar ventanas antiguas
        old_keys = [k for k in self._request_counts if not k.endswith(f":{current_window}")]
        for old_key in old_keys:
            self._request_counts.pop(old_key, None)
        
        # Incrementar contador
        self._request_counts[key] = self._request_counts.get(key, 0) + 1
        
        if self._request_counts[key] > self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit excedido: {self.calls} llamadas por {self.period}s"
            )


def rate_limit(
    calls: int = 60,
    period: int = 60
) -> RateLimiter:
    """
    Dependency para rate limiting.
    
    Args:
        calls: Número de llamadas permitidas
        period: Período en segundos
    
    Returns:
        RateLimiter: Rate limiter configurado
    """
    return RateLimiter(calls=calls, period=period)