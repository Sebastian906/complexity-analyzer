"""
Configuración Central del Sistema

Gestiona todas las configuraciones de la aplicación usando Pydantic Settings.
Carga variables de entorno y proporciona validación de tipos.
"""

import secrets
from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración principal de la aplicación.
    
    Todos los valores pueden ser sobrescritos mediante variables de entorno.
    """
    
    # Configuración de la Aplicación
    APP_NAME: str = "Complexity Analyzer API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: Literal["development", "staging", "production", "testing"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    
    # Configuración del Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "PATCH"])
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"]
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parsea CORS_ORIGINS si viene como string JSON"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v
    
    # Seguridad
    SECRET_KEY: str = Field(default="")
    API_KEY_HEADER: str = "X-API-Key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM APIs - Claude (Anthropic)
    ANTHROPIC_API_KEY: str = Field(default="")
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 4000
    CLAUDE_TEMPERATURE: float = 0.0
    
    # LLM APIs - Google Gemini
    GOOGLE_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_MAX_TOKENS: int = 4000
    GEMINI_TEMPERATURE: float = 0.0
    
    # Configuración LLM
    PRIMARY_LLM: Literal["claude", "gemini"] = "gemini"
    FALLBACK_LLM: Literal["claude", "gemini"] = "claude"
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: int = 2
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "complexity_analyzer"
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_POOL_SIZE: int = 50
    MONGODB_ALGORITHMS_COLLECTION: str = "algorithms"
    MONGODB_ANALYSIS_COLLECTION: str = "analysis_results"
    MONGODB_PATTERNS_COLLECTION: str = "pattern_detections"
    
    # PostgreSQL (Alternativa)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "complexity_analyzer"
    POSTGRES_ECHO: bool = False
    POSTGRES_POOL_SIZE: int = 20
    POSTGRES_MAX_OVERFLOW: int = 0
    
    @property
    def DATABASE_URL(self) -> str:
        """Construye la URL de PostgreSQL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_DECODE_RESPONSES: bool = True
    REDIS_MAX_CONNECTIONS: int = 50
    
    # TTL de caché (en segundos)
    CACHE_TTL_ANALYSIS: int = 3600  # 1 hora
    CACHE_TTL_PATTERN: int = 7200   # 2 horas
    CACHE_TTL_LLM: int = 1800       # 30 minutos
    
    @property
    def REDIS_URL(self) -> str:
        """Construye la URL de Redis"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Parser
    PARSER_TIMEOUT: int = 10
    MAX_ALGORITHM_LINES: int = 1000
    MAX_ALGORITHM_SIZE_KB: int = 100
    
    # Análisis
    ANALYSIS_TIMEOUT: int = 60
    MAX_RECURSION_DEPTH: int = 1000
    ENABLE_SYMBOLIC_SOLVING: bool = True
    
    # Visualización
    MAX_TREE_DEPTH: int = 10
    MAX_TREE_NODES: int = 100
    GRAPHVIZ_ENGINE: Literal["dot", "neato", "fdp", "sfdp", "circo", "twopi"] = "dot"
    
    # Exportación
    EXPORT_PDF_ENABLED: bool = True
    EXPORT_JSON_ENABLED: bool = True
    EXPORT_MARKDOWN_ENABLED: bool = True
    EXPORT_EXCEL_ENABLED: bool = True
    EXPORT_HTML_ENABLED: bool = True
    
    # Profiling
    ENABLE_PROFILING: bool = True
    PROFILE_MEMORY: bool = False  # True solo en debugging
    PROFILE_EXECUTION_TIME: bool = True

    # Almacenamiento de Archivos
    STORAGE_PATH: Path = Field(default=Path("./data"))
    MAX_UPLOAD_SIZE_MB: int = 5
    
    @property
    def ALGORITHMS_PATH(self) -> Path:
        """Ruta de algoritmos guardados"""
        return self.STORAGE_PATH / "algorithms"

    EXPORTS_BASE_DIR: str = Field(
        default="data/exports",
        description="Directorio base para archivos exportados"
    )
    
    @property
    def EXPORTS_PATH(self) -> Path:
        """
        Retorna el Path al directorio base de exports.
        Se crea automáticamente si no existe.
        """
        base_path = Path(self.EXPORTS_BASE_DIR)
        if not base_path.is_absolute():
            # Si es relativo, lo resolvemos desde la raíz del proyecto
            base_path = Path(__file__).parent.parent.parent / base_path
        
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path
    
    def get_export_path(self, format: str) -> Path:
        """
        Retorna el Path al directorio específico según el formato.
        
        Args:
            format: Formato de exportación (json, pdf, markdown, etc.)
        
        Returns:
            Path al directorio del formato específico
        
        Example:
            >>> settings.get_export_path("json")
            Path("data/exports/json")
        """
        format_path = self.EXPORTS_PATH / format.lower()
        format_path.mkdir(parents=True, exist_ok=True)
        return format_path
    
    @property
    def TEMP_PATH(self) -> Path:
        """Ruta de archivos temporales"""
        return self.STORAGE_PATH / "temp"
    
    # Logging
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    LOG_FILE_PATH: Path = Field(default=Path("./logs/app.log"))
    LOG_ROTATION: str = "00:00"
    LOG_RETENTION: str = "30 days"
    LOG_COMPRESSION: str = "zip"
    
    # Monitoreo
    ENABLE_PROMETHEUS: bool = False
    PROMETHEUS_PORT: int = 9090
    ENABLE_SENTRY: bool = False
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    
    @property
    def SENTRY_ENVIRONMENT(self) -> str:
        """Retorna el entorno para Sentry"""
        return self.APP_ENV
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Testing
    TEST_MODE: bool = False
    MOCK_LLM_RESPONSES: bool = False
    
    # Feature Flags
    ENABLE_MULTIAGENT_SYSTEM: bool = False
    ENABLE_DATASET_GENERATOR: bool = False
    ENABLE_ADVANCED_PATTERNS: bool = True
    ENABLE_SPATIAL_COMPLEXITY: bool = True
    ENABLE_TIGHT_BOUNDS: bool = True
    
    # Selección de Base de Datos
    DATABASE_TYPE: Literal["mongodb", "postgresql"] = "mongodb"

    # Sistema de Detección de Intrusiones ─────────────────────────────────
    IDS_ENABLED: bool = Field(default=True)
    IDS_INTERFACE: str = Field(default="")          # vacío = interfaz default del SO
    IDS_THREAT_TTL_SECONDS: int = Field(default=300)
    IDS_MAX_THREATS_BEFORE_BLOCK: int = Field(default=10)
    IDS_PERSIST_TO_MONGODB: bool = Field(default=False)
    IDS_WINDOW_SECONDS: float = Field(default=10.0)  # ventana de análisis de tráfico
    
    # Configuración de Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def model_post_init(self, __context):
        """Post-inicialización: validar secretos y crear directorios necesarios"""
        # --- Validación de secretos ---
        _INSECURE_DEFAULTS = {"", "CHANGE-ME-IN-PRODUCTION-PLEASE"}

        if self.is_production:
            # En producción, SECRET_KEY DEBE ser proporcionada explícitamente
            if self.SECRET_KEY in _INSECURE_DEFAULTS:
                raise ValueError(
                    "SECRET_KEY no está configurada. "
                    "Defina una clave segura en la variable de entorno SECRET_KEY "
                    "antes de ejecutar en producción."
                )
            if not self.POSTGRES_PASSWORD:
                raise ValueError(
                    "POSTGRES_PASSWORD no está configurada. "
                    "Defina la contraseña de la base de datos en la variable de entorno "
                    "POSTGRES_PASSWORD antes de ejecutar en producción."
                )
            if self.DEBUG:
                raise ValueError(
                    "DEBUG está activado en producción. "
                    "Defina DEBUG=False en las variables de entorno "
                    "antes de ejecutar en producción."
                )
        else:
            # En desarrollo/testing, generar SECRET_KEY segura si no fue configurada
            if self.SECRET_KEY in _INSECURE_DEFAULTS:
                object.__setattr__(self, "SECRET_KEY", secrets.token_hex(32))

        # Crear directorios si no existen
        self.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        self.ALGORITHMS_PATH.mkdir(parents=True, exist_ok=True)
        self.EXPORTS_PATH.mkdir(parents=True, exist_ok=True)
        self.TEMP_PATH.mkdir(parents=True, exist_ok=True)
        self.LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        """Verifica si está en modo desarrollo"""
        return self.APP_ENV == "development"
    
    @property
    def is_production(self) -> bool:
        """Verifica si está en modo producción"""
        return self.APP_ENV == "production"
    
    @property
    def is_testing(self) -> bool:
        """Verifica si está en modo testing"""
        return self.APP_ENV == "testing"


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton para obtener las configuraciones.
    
    Usa lru_cache para garantizar una única instancia.
    
    Returns:
        Settings: Instancia de configuración
        
    Example:
        >>> from app.core.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.APP_NAME)
    """
    return Settings()


# Instancia global para importación directa
settings = get_settings()