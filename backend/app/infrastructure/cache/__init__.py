"""
Cache Infrastructure Package

Proporciona:
- RedisCache: Cliente Redis
- CacheRepository: Repositorio de caché
- cache_keys: Definiciones de claves
"""

from .redis_cache import RedisCache, get_redis_client
from .cache_keys import (
    CachePrefix,
    CacheTTL,
    build_analysis_key,
    build_complexity_key,
    build_recurrence_key,
    build_pattern_key,
    build_pattern_score_key,
    build_structure_key,
    build_llm_key,
    build_llm_validation_key,
    build_tree_key,
    build_graph_key,
    build_diagram_key,
    build_algorithm_key,
    build_algorithm_list_key,
    build_algorithm_search_key,
    build_user_key,
    build_user_session_key,
    build_user_permissions_key,
    build_metrics_key,
    build_stats_key,
    build_temp_key,
    build_lock_key,
    hash_content,
    build_composite_key,
    parse_key,
    get_key_prefix,
)

__all__ = [
    # Redis Client
    "RedisCache",
    "get_redis_client",
    
    # Cache Keys
    "CachePrefix",
    "CacheTTL",
    
    # Key Builders
    "build_analysis_key",
    "build_complexity_key",
    "build_recurrence_key",
    "build_pattern_key",
    "build_pattern_score_key",
    "build_structure_key",
    "build_llm_key",
    "build_llm_validation_key",
    "build_tree_key",
    "build_graph_key",
    "build_diagram_key",
    "build_algorithm_key",
    "build_algorithm_list_key",
    "build_algorithm_search_key",
    "build_user_key",
    "build_user_session_key",
    "build_user_permissions_key",
    "build_metrics_key",
    "build_stats_key",
    "build_temp_key",
    "build_lock_key",
    
    # Helpers
    "hash_content",
    "build_composite_key",
    "parse_key",
    "get_key_prefix",
]