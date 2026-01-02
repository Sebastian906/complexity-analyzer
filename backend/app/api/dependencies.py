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
    
    async def __call__(self) -> None:
        """Verifica rate limit"""
        # TODO: Implementar con Redis
        pass


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