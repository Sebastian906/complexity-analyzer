"""
DynamicConfig — Configuración dinámica recargable sin redeploy.

Permite cambiar comportamiento del sistema editando un archivo YAML
o una clave Redis, sin reiniciar el servidor.

Jerarquía de fuentes (orden de prioridad):
    1. Redis key "runtime_flags" (si Redis está disponible)
    2. Archivo config/runtime_flags.yaml
    3. Defaults hardcodeados en esta clase

Recarga automática cada TTL_SECONDS (default: 60s).
Si la fuente falla, mantiene la configuración anterior en lugar de crashear.

Uso:
    from app.services.dynamic_config import DynamicConfig

    if DynamicConfig.get("llm_validation_enabled", False):
        routed = await router.route(prompt)

    llm = DynamicConfig.get("primary_llm", "ollama")

Cambiar en runtime (sin redeploy):
    # Opción 1: editar config/runtime_flags.yaml y esperar 60s
    # Opción 2: desde Redis CLI:
    #   redis-cli SET runtime_flags '{"llm_validation_enabled": true}'
    #   redis-cli EXPIRE runtime_flags 3600
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Ruta del archivo de flags
_FLAGS_FILE = Path("config/runtime_flags.yaml")

# Clave Redis donde se almacenan los flags
_REDIS_KEY = "runtime_flags"

# Intervalo de recarga en segundos
TTL_SECONDS = 60

# Defaults si no hay archivo ni Redis
_DEFAULTS: dict[str, Any] = {
    # LLM
    "primary_llm":               "ollama",
    "fallback_llm":              "gemini",
    "llm_validation_enabled":    False,
    "llm_min_acceptable_score":  0.6,
    "llm_timeout_seconds":       30.0,

    # Pipeline
    "pipeline_steps_enabled": {
        "parse":          True,
        "complexity":     True,
        "patterns":       True,
        "structures":     True,
        "llm_validation": False,
        "summarize":      True,
        "visualizations": False,
    },

    # Cache
    "cache_enabled":        True,
    "cache_ttl_analysis":   3600,
    "cache_ttl_patterns":   7200,

    # Análisis
    "multiagent_enabled":   False,
    "min_confidence":       0.3,
}

class DynamicConfig:
    """
    Configuración dinámica del sistema.

    Clase de métodos de clase — no instanciar, usar DynamicConfig.get().

    Todos los métodos son thread-safe para uso en contextos async
    (asyncio es single-threaded, pero la recarga puede ocurrir desde
    cualquier coroutine en cualquier momento).
    """

    _cache: dict[str, Any] = {}
    _last_loaded: float = 0.0
    _load_errors: int = 0  # Contador para reducir spam de logs

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Obtiene el valor de una flag de configuración.

        Si la configuración no se ha cargado o está expirada,
        la recarga de forma transparente.

        Args:
            key:     Nombre de la flag (e.g. "llm_validation_enabled").
            default: Valor si la flag no existe.

        Returns:
            Valor de la flag o default.

        Example:
            >>> DynamicConfig.get("llm_validation_enabled", False)
            False
            >>> DynamicConfig.get("pipeline_steps_enabled.parse", True)
            True
        """
        cls._maybe_reload()

        # Soporte para claves anidadas con notación punto
        if "." in key:
            parts = key.split(".", 1)
        else:
            parts = [key]

        value = cls._cache
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
            if value is None:
                return default

        return value if value is not None else default

    @classmethod
    def get_all(cls) -> dict[str, Any]:
        """Retorna toda la configuración activa (para debugging y /health)."""
        cls._maybe_reload()
        return dict(cls._cache)

    @classmethod
    def reload(cls) -> bool:
        """
        Fuerza una recarga inmediata.

        Returns:
            True si la recarga fue exitosa.

        Example:
            # Después de actualizar Redis o el archivo YAML:
            DynamicConfig.reload()
        """
        return cls._reload()

    @classmethod
    def is_step_enabled(cls, step_name: str) -> bool:
        """
        Verifica si un paso del pipeline está habilitado.

        Shortcut para:
            DynamicConfig.get(f"pipeline_steps_enabled.{step_name}", True)

        Args:
            step_name: Nombre del paso ("parse", "complexity", etc.)

        Returns:
            True si el paso está habilitado (default: True para compatibilidad).
        """
        steps = cls.get("pipeline_steps_enabled", {})
        if isinstance(steps, dict):
            return steps.get(step_name, True)
        return True

    #  Internos                                                           
    @classmethod
    def _maybe_reload(cls) -> None:
        """Recarga si el TTL expiró."""
        if time.time() - cls._last_loaded > TTL_SECONDS:
            cls._reload()

    @classmethod
    def _reload(cls) -> bool:
        """
        Intenta recargar desde Redis → YAML → defaults.

        Nunca lanza excepción — mantiene config anterior si falla.
        """
        new_config = dict(_DEFAULTS)  # Empezar desde defaults

        loaded = False

        # Fuente 1: Redis
        if not loaded:
            loaded = cls._try_load_from_redis(new_config)

        # Fuente 2: Archivo YAML
        if not loaded:
            loaded = cls._try_load_from_file(new_config)

        # Siempre actualizar aunque no haya cargado nada nuevo
        # (para resetear el TTL y no recargar en cada llamada)
        cls._cache = new_config
        cls._last_loaded = time.time()

        if loaded:
            cls._load_errors = 0
        else:
            cls._load_errors += 1
            if cls._load_errors == 1:
                logger.debug(
                    "DynamicConfig: usando defaults "
                    "(ni Redis ni YAML disponibles)"
                )

        return loaded

    @classmethod
    def _try_load_from_redis(cls, target: dict) -> bool:
        """Intenta cargar desde Redis. Retorna True si tuvo éxito."""
        try:
            import redis
            from app.core.config import settings

            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                socket_connect_timeout=1.0,
            )
            data = r.get(_REDIS_KEY)
            if data:
                parsed = json.loads(data)
                target.update(parsed)
                logger.debug(
                    f"DynamicConfig: cargado desde Redis "
                    f"({len(parsed)} flags)"
                )
                return True
        except Exception:
            pass  # Redis no disponible — intentar YAML
        return False

    @classmethod
    def _try_load_from_file(cls, target: dict) -> bool:
        """Intenta cargar desde el archivo YAML. Retorna True si tuvo éxito."""
        try:
            if not _FLAGS_FILE.exists():
                return False

            import yaml

            with _FLAGS_FILE.open(encoding="utf-8") as f:
                parsed = yaml.safe_load(f)

            if parsed and isinstance(parsed, dict):
                target.update(parsed)
                logger.debug(
                    f"DynamicConfig: cargado desde {_FLAGS_FILE} "
                    f"({len(parsed)} flags)"
                )
                return True
        except Exception as exc:
            logger.warning(f"DynamicConfig: error leyendo YAML — {exc}")
        return False