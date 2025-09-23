"""
Inicialização do módulo de cache
"""

from .cache_utils import cache_manager, CacheKeys, CacheManager, cache_response
from .mixins import (
    CacheInvalidationMixin,
    ListCacheMixin,
    DetailCacheMixin,
    CompleteCacheMixin,
)
from .signals import manual_cache_invalidation, get_cache_stats

__all__ = [
    "cache_manager",
    "CacheKeys",
    "CacheManager",
    "cache_response",
    "CacheInvalidationMixin",
    "ListCacheMixin",
    "DetailCacheMixin",
    "CompleteCacheMixin",
    "manual_cache_invalidation",
    "get_cache_stats",
]
