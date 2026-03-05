"""
Middlewares Personalizados para FastAPI

Proporciona middlewares custom para logging, rate limiting, 
autenticación, CORS avanzado y manejo de requests.
"""

import time
import uuid
from typing import Callable, Optional, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.exceptions import RateLimitException, AuthenticationException
from app.utils.logger import get_logger

logger = get_logger(__name__)

# REQUEST ID MIDDLEWARE
class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware para agregar un ID único a cada request.
    
    Útil para tracking y debugging de requests específicas.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesar request agregando X-Request-ID"""
        # Generar o extraer request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Agregar al state del request
        request.state.request_id = request_id
        
        # Procesar request
        response = await call_next(request)
        
        # Agregar header a la respuesta
        response.headers["X-Request-ID"] = request_id
        
        return response

# LOGGING MIDDLEWARE
class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging detallado de todas las requests.
    
    Loggea método, path, status code, duración y errores.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Loggear información de la request y response"""
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Información de la request
        logger.info(
            f"Request iniciada: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
            }
        )
        
        try:
            # Procesar request
            response = await call_next(request)
            
            # Calcular duración
            duration = time.time() - start_time
            
            # Loggear respuesta exitosa
            logger.info(
                f"Request completada: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration:.4f}s",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                }
            )
            
            return response
            
        except Exception as e:
            # Loggear error
            duration = time.time() - start_time
            logger.error(
                f"Request fallida: {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration:.4f}s",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration": duration,
                }
            )
            raise

# RATE LIMITING MIDDLEWARE
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware para rate limiting basado en IP.
    
    Limita el número de requests por IP en una ventana de tiempo.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Storage para tracking (en producción usar Redis)
        self.minute_tracker: Dict[str, list] = defaultdict(list)
        self.hour_tracker: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Verificar rate limits antes de procesar request"""
        # Si está deshabilitado o en modo debug/testing, pasar directo
        if not settings.RATE_LIMIT_ENABLED or settings.DEBUG:
            return await call_next(request)
        
        # Obtener IP del cliente
        client_ip = self._get_client_ip(request)
        
        # Verificar límites
        now = datetime.now()
        
        # Limpiar registros antiguos
        self._cleanup_old_requests(client_ip, now)
        
        # Verificar límite por minuto
        if len(self.minute_tracker[client_ip]) >= self.requests_per_minute:
            logger.warning(
                f"Rate limit excedido (por minuto): {client_ip}",
                extra={"client_ip": client_ip, "limit": "minute"}
            )
            return self._rate_limit_response(
                self.requests_per_minute,
                "minuto"
            )
        
        # Verificar límite por hora
        if len(self.hour_tracker[client_ip]) >= self.requests_per_hour:
            logger.warning(
                f"Rate limit excedido (por hora): {client_ip}",
                extra={"client_ip": client_ip, "limit": "hour"}
            )
            return self._rate_limit_response(
                self.requests_per_hour,
                "hora"
            )
        
        # Registrar request
        self.minute_tracker[client_ip].append(now)
        self.hour_tracker[client_ip].append(now)
        
        # Procesar request
        response = await call_next(request)
        
        # Agregar headers de rate limit
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            self.requests_per_minute - len(self.minute_tracker[client_ip])
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            self.requests_per_hour - len(self.hour_tracker[client_ip])
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP del cliente (considerando proxies)"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_ip: str, now: datetime):
        """Limpiar requests antiguos fuera de la ventana de tiempo"""
        # Limpiar requests de hace más de 1 minuto
        minute_ago = now - timedelta(minutes=1)
        self.minute_tracker[client_ip] = [
            req_time for req_time in self.minute_tracker[client_ip]
            if req_time > minute_ago
        ]
        
        # Limpiar requests de hace más de 1 hora
        hour_ago = now - timedelta(hours=1)
        self.hour_tracker[client_ip] = [
            req_time for req_time in self.hour_tracker[client_ip]
            if req_time > hour_ago
        ]
    
    def _rate_limit_response(self, limit: int, window: str) -> JSONResponse:
        """Crear respuesta de rate limit excedido"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "error": {
                    "type": "RateLimitExceeded",
                    "message": f"Se excedió el límite de {limit} requests por {window}",
                    "limit": limit,
                    "window": window,
                }
            },
            headers={
                "Retry-After": "60" if window == "minuto" else "3600"
            }
        )

# SECURITY HEADERS MIDDLEWARE
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware para agregar headers de seguridad estándar.
    
    Agrega headers como X-Content-Type-Options, X-Frame-Options, etc.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Agregar security headers a la respuesta"""
        response = await call_next(request)
        
        # Security headers estándar
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        
        # Content Security Policy (básico)
        if not settings.DEBUG:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'"
            )
        
        return response

# API KEY VALIDATION MIDDLEWARE
class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware para validar API keys en requests.
    
    Solo se aplica si SECRET_KEY está configurado y no es desarrollo.
    """
    
    # Rutas públicas que no requieren API key
    PUBLIC_PATHS = [
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validar API key antes de procesar request"""
        # Saltar validación en desarrollo o si no hay SECRET_KEY
        if settings.DEBUG or not settings.SECRET_KEY:
            return await call_next(request)
        
        # Verificar si la ruta es pública
        if any(request.url.path.startswith(path) for path in self.PUBLIC_PATHS):
            return await call_next(request)
        
        # Extraer API key del header
        api_key = request.headers.get(settings.API_KEY_HEADER)
        
        # Validar API key
        if not api_key or api_key != settings.SECRET_KEY:
            logger.warning(
                f"API key inválida o ausente: {request.url.path}",
                extra={
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else None,
                }
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "type": "Unauthorized",
                        "message": "API key inválida o ausente",
                    }
                }
            )
        
        return await call_next(request)

# CORS ADVANCED MIDDLEWARE
class CORSAdvancedMiddleware(BaseHTTPMiddleware):
    """
    Middleware CORS avanzado con control granular.
    
    Complementa el CORSMiddleware de FastAPI con lógica adicional.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Manejar CORS con lógica avanzada"""
        # Obtener origin
        origin = request.headers.get("Origin")
        
        # Si no hay origin, continuar normal
        if not origin:
            return await call_next(request)
        
        # Validar origin contra whitelist
        if not self._is_origin_allowed(origin):
            logger.warning(
                f"CORS: Origin no permitido: {origin}",
                extra={"origin": origin, "path": request.url.path}
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "error": {
                        "type": "CORSError",
                        "message": "Origin no permitido",
                    }
                }
            )
        
        # Procesar request
        response = await call_next(request)
        
        # Agregar headers CORS adicionales
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = (
            "X-Request-ID, X-Process-Time, X-RateLimit-Remaining-Minute"
        )
        
        return response
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Verificar si el origin está permitido"""
        # Permitir todos los origins en desarrollo
        if settings.DEBUG:
            return True
        
        # Verificar contra la lista de origins permitidos
        allowed_origins = settings.CORS_ORIGINS
        
        # Permitir wildcards simples
        for allowed in allowed_origins:
            if allowed == "*":
                return True
            if allowed.endswith("*"):
                if origin.startswith(allowed[:-1]):
                    return True
            elif origin == allowed:
                return True
        
        return False

# CACHE CONTROL MIDDLEWARE
class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware para agregar headers de control de caché.
    
    Configura políticas de caché según el tipo de endpoint.
    """
    
    # Configuración de caché por path pattern
    CACHE_CONFIG = {
        "/api/v1/health": {"max-age": 60, "public": True},
        "/api/v1/analysis": {"max-age": 3600, "public": False},
        "/api/v1/patterns": {"max-age": 7200, "public": False},
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Agregar cache control headers"""
        response = await call_next(request)
        
        # No cachear en desarrollo
        if settings.DEBUG:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            return response
        
        # Encontrar configuración de caché para este path
        cache_config = self._get_cache_config(request.url.path)
        
        if cache_config:
            # Construir header Cache-Control
            cache_parts = []
            
            if cache_config.get("public"):
                cache_parts.append("public")
            else:
                cache_parts.append("private")
            
            max_age = cache_config.get("max-age", 0)
            cache_parts.append(f"max-age={max_age}")
            
            response.headers["Cache-Control"] = ", ".join(cache_parts)
        else:
            # Default: no-cache para endpoints no configurados
            response.headers["Cache-Control"] = "no-cache"
        
        return response
    
    def _get_cache_config(self, path: str) -> Optional[Dict[str, Any]]:
        """Obtener configuración de caché para un path"""
        for pattern, config in self.CACHE_CONFIG.items():
            if path.startswith(pattern):
                return config
        return None

# COMPRESSION MIDDLEWARE (adicional a GZipMiddleware)
class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware para agregar información sobre compresión.
    
    Complementa GZipMiddleware con headers adicionales.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Agregar información de compresión"""
        response = await call_next(request)
        
        # Agregar header Vary para proxies
        response.headers["Vary"] = "Accept-Encoding"
        
        return response

# ERROR HANDLING MIDDLEWARE
class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para manejo centralizado de errores no capturados.
    
    Catch-all para errores que escapan los exception handlers.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Capturar y manejar errores no esperados"""
        try:
            return await call_next(request)
        except Exception as e:
            # Loggear error
            request_id = getattr(request.state, "request_id", "unknown")
            logger.exception(
                f"Error no manejado en request {request_id}",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": type(e).__name__,
                }
            )
            
            # Retornar respuesta de error genérica
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "type": "InternalServerError",
                        "message": "Error interno del servidor",
                        "request_id": request_id,
                        "details": str(e) if settings.DEBUG else None,
                    }
                }
            )