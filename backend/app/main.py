"""
Entry Point Principal - FastAPI Application

Este es el punto de entrada de la aplicación FastAPI.
Configura middlewares, routers, eventos de inicio/apagado y documentación.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    ComplexityAnalyzerException,
    DatabaseException,
    LLMException,
    ParserException,
)
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Gestor de ciclo de vida de la aplicación.
    
    Maneja eventos de inicio y apagado de manera asíncrona.
    """
    # STARTUP - Inicialización
    logger.info(f"Iniciando {settings.APP_NAME} v{__version__}")
    logger.info(f"Entorno: {settings.APP_ENV}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    try:
        # Inicializar conexiones a bases de datos
        logger.info("Conectando a bases de datos...")
        
        if settings.DATABASE_TYPE == "mongodb":
            from app.infrastructure.database.mongodb_client import get_mongodb_client
            await get_mongodb_client().connect()
            logger.info("MongoDB conectado")
        
        elif settings.DATABASE_TYPE == "postgresql":
            from app.infrastructure.database.postgresql_client import get_postgresql_client
            await get_postgresql_client().connect()
            logger.info("PostgreSQL conectado")
        
        # Inicializar Redis (si está habilitado)
        if settings.REDIS_HOST:
            from app.infrastructure.cache.redis_cache import get_redis_client
            await get_redis_client().ping()
            logger.info("Redis conectado")
        
        # Verificar APIs de LLMs
        if settings.ANTHROPIC_API_KEY:
            logger.info("Claude API configurada")
        if settings.GOOGLE_API_KEY:
            logger.info("Gemini API configurada")
        
        logger.info("Aplicación iniciada correctamente")
        
    except Exception as e:
        logger.error(f"Error durante el inicio: {e}")
        raise
    
    yield  # La aplicación corre aquí
    
    # SHUTDOWN - Limpieza
    logger.info("Cerrando aplicación...")
    
    try:
        # Cerrar conexiones a bases de datos
        if settings.DATABASE_TYPE == "mongodb":
            from app.infrastructure.database.mongodb_client import get_mongodb_client
            await get_mongodb_client().close()
            logger.info("MongoDB desconectado")
        
        elif settings.DATABASE_TYPE == "postgresql":
            from app.infrastructure.database.postgresql_client import get_postgresql_client
            await get_postgresql_client().close()
            logger.info("PostgreSQL desconectado")
        
        # Cerrar Redis
        if settings.REDIS_HOST:
            from app.infrastructure.cache.redis_cache import get_redis_client
            await get_redis_client().close()
            logger.info("Redis desconectado")
        
        logger.info("Aplicación cerrada correctamente")
        
    except Exception as e:
        logger.error(f"Error durante el cierre: {e}")

# Crear aplicación FastAPI

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API REST para análisis automático de complejidad algorítmica "
        "asistido por Large Language Models (LLMs)"
    ),
    version=__version__,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Middlewares

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Compresión GZip
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Middleware de timing de requests
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Agrega header con tiempo de procesamiento"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# Middleware de logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Loggea todas las requests"""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code}")
    return response

# Exception Handlers

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler para excepciones HTTP estándar"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para errores de validación de Pydantic"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "type": "ValidationError",
                "message": "Error de validación en los datos de entrada",
                "details": exc.errors(),
            }
        },
    )

@app.exception_handler(ParserException)
async def parser_exception_handler(request: Request, exc: ParserException):
    """Handler para errores del parser"""
    logger.error(f"Parser Error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "type": "ParserError",
                "message": exc.message,
                "details": exc.details,
            }
        },
    )

@app.exception_handler(LLMException)
async def llm_exception_handler(request: Request, exc: LLMException):
    """Handler para errores de LLMs"""
    logger.error(f"LLM Error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error": {
                "type": "LLMError",
                "message": exc.message,
                "details": exc.details,
            }
        },
    )

@app.exception_handler(DatabaseException)
async def database_exception_handler(request: Request, exc: DatabaseException):
    """Handler para errores de base de datos"""
    logger.error(f"Database Error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "type": "DatabaseError",
                "message": "Error de base de datos",
                "details": exc.details if settings.DEBUG else None,
            }
        },
    )

@app.exception_handler(ComplexityAnalyzerException)
async def complexity_analyzer_exception_handler(request: Request, exc: ComplexityAnalyzerException):
    """Handler para excepciones generales del analizador"""
    logger.error(f"Complexity Analyzer Error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "type": "ComplexityAnalyzerError",
                "message": exc.message,
                "details": exc.details if settings.DEBUG else None,
            }
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para excepciones no controladas"""
    logger.exception(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "type": "InternalServerError",
                "message": "Error interno del servidor",
                "details": str(exc) if settings.DEBUG else None,
            }
        },
    )

# Routers

# Incluir router principal de la API
app.include_router(api_router, prefix=f"/api/v1")

# Root Endpoint

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz de la API.
    
    Retorna información básica de la aplicación.
    """
    return {
        "name": settings.APP_NAME,
        "version": __version__,
        "environment": settings.APP_ENV,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else None,
        "api": {
            "v1": "/api/v1",
        }
    }

# Ejecutar aplicación

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        workers=settings.WORKERS if not settings.RELOAD else 1,
    )