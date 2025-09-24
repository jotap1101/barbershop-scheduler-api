"""
Cache utilities para a API Django REST Framework

Este módulo fornece utilitários para cache inteligente e invalidação
Suporta tanto DatabaseCache quanto Redis com funcionalidades avançadas
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, List, Optional, Union

from django.conf import settings
from django.core.cache import cache, caches
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class CacheKeys:
    """Constantes para chaves de cache organizadas por contexto"""

    # Prefixes para diferentes tipos de dados
    BARBERSHOP_PREFIX = "barbershop"
    SERVICE_PREFIX = "service"
    APPOINTMENT_PREFIX = "appointment"
    USER_PREFIX = "user"
    REVIEW_PREFIX = "review"
    SEARCH_PREFIX = "search"

    # Cache keys para listagens
    BARBERSHOP_LIST = f"{BARBERSHOP_PREFIX}:list"
    SERVICE_LIST = f"{SERVICE_PREFIX}:list"
    BARBERSHOP_SERVICES = f"{BARBERSHOP_PREFIX}:services"
    AVAILABLE_SLOTS = f"{APPOINTMENT_PREFIX}:slots"

    # Cache keys para detalhes
    BARBERSHOP_DETAIL = f"{BARBERSHOP_PREFIX}:detail"
    SERVICE_DETAIL = f"{SERVICE_PREFIX}:detail"
    USER_PROFILE = f"{USER_PREFIX}:profile"

    # Cache keys para dados agregados
    BARBERSHOP_STATS = f"{BARBERSHOP_PREFIX}:stats"
    POPULAR_SERVICES = f"{SERVICE_PREFIX}:popular"
    REVIEWS_SUMMARY = f"{REVIEW_PREFIX}:summary"


class CacheManager:
    """Gerenciador centralizado de cache com funcionalidades avançadas"""

    def __init__(self, cache_name: str = "default"):
        self.cache = caches[cache_name]
        self.ttl_config = getattr(settings, "CACHE_TTL", {})
        self._redis_client = None

    @property
    def redis_client(self):
        """Acesso direto ao cliente Redis para operações avançadas"""
        if self._redis_client is None and self.is_redis_backend():
            try:
                from django_redis import get_redis_connection

                self._redis_client = get_redis_connection("default")
            except ImportError:
                logger.warning("django-redis não disponível")
        return self._redis_client

    def is_redis_backend(self) -> bool:
        """Verifica se está usando Redis como backend"""
        backend = settings.CACHES.get("default", {}).get("BACKEND", "")
        return "redis" in backend.lower()

    def get_backend_info(self) -> dict:
        """Retorna informações sobre o backend de cache atual"""
        cache_config = settings.CACHES.get("default", {})
        info = {
            "backend": cache_config.get("BACKEND", "Unknown"),
            "is_redis": self.is_redis_backend(),
            "location": cache_config.get("LOCATION", "N/A"),
        }

        if self.is_redis_backend() and self.redis_client:
            try:
                redis_info = self.redis_client.info()
                info.update(
                    {
                        "redis_version": redis_info.get("redis_version"),
                        "used_memory": redis_info.get("used_memory_human"),
                        "connected_clients": redis_info.get("connected_clients"),
                        "total_commands_processed": redis_info.get(
                            "total_commands_processed"
                        ),
                        "keyspace_hits": redis_info.get("keyspace_hits", 0),
                        "keyspace_misses": redis_info.get("keyspace_misses", 0),
                    }
                )

                # Calcular hit rate
                hits = info.get("keyspace_hits", 0)
                misses = info.get("keyspace_misses", 0)
                if hits + misses > 0:
                    info["hit_rate"] = f"{(hits / (hits + misses)) * 100:.2f}%"
            except Exception as e:
                logger.error(f"Erro ao obter info do Redis: {e}")

        return info

    def get_ttl(self, ttl_type: str) -> int:
        """Retorna TTL baseado no tipo configurado"""
        return self.ttl_config.get(ttl_type, self.ttl_config.get("MEDIUM", 1800))

    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Gera chave de cache consistente baseada nos parâmetros"""
        key_parts = [prefix]

        # Adiciona parâmetros ordenados
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (dict, list)):
                # Para objetos complexos, usa hash
                value_str = hashlib.md5(
                    json.dumps(value, sort_keys=True).encode()
                ).hexdigest()[:8]
            else:
                value_str = str(value)
            key_parts.append(f"{key}:{value_str}")

        return ":".join(key_parts)

    def get_or_set_cache(
        self, key: str, fetch_func: Callable, ttl_type: str = "MEDIUM", **fetch_kwargs
    ) -> Any:
        """
        Busca dados do cache ou executa função para obter/cachear

        Args:
            key: Chave do cache
            fetch_func: Função para buscar dados se não estiver em cache
            ttl_type: Tipo de TTL (SHORT, MEDIUM, LONG, LISTING)
            **fetch_kwargs: Argumentos para a função de busca
        """
        cached_data = self.cache.get(key)

        if cached_data is not None:
            return cached_data

        # Busca dados e coloca no cache
        data = fetch_func(**fetch_kwargs)
        ttl = self.get_ttl(ttl_type)
        self.cache.set(key, data, ttl)

        return data

    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Lista chaves por padrão (funciona apenas com Redis)"""
        if not self.is_redis_backend() or not self.redis_client:
            logger.warning("get_keys_by_pattern só funciona com Redis backend")
            return []

        try:
            key_prefix = settings.CACHES["default"].get("KEY_PREFIX", "")
            version = settings.CACHES["default"].get("VERSION", 1)

            # Construir padrão completo com prefixo e versão
            if key_prefix:
                full_pattern = f"{key_prefix}:{version}:*{pattern}*"
            else:
                full_pattern = f"*{pattern}*"

            keys = self.redis_client.keys(full_pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.error(f"Erro ao buscar chaves por padrão: {e}")
            return []

    def clear_pattern(self, pattern: str) -> int:
        """
        Limpa cache por padrão

        Args:
            pattern: Padrão para buscar chaves

        Returns:
            Número de chaves removidas
        """
        if self.is_redis_backend() and self.redis_client:
            # Redis: suporte nativo para padrões
            try:
                keys = self.get_keys_by_pattern(pattern)
                if keys:
                    # Remover prefixo e versão para usar com Django cache
                    cleaned_keys = []
                    key_prefix = settings.CACHES["default"].get("KEY_PREFIX", "")
                    version = settings.CACHES["default"].get("VERSION", 1)

                    for key in keys:
                        if key_prefix:
                            # Remove prefixo:versão: do início
                            prefix_pattern = f"{key_prefix}:{version}:"
                            if key.startswith(prefix_pattern):
                                cleaned_key = key[len(prefix_pattern) :]
                                cleaned_keys.append(cleaned_key)
                        else:
                            cleaned_keys.append(key)

                    self.cache.delete_many(cleaned_keys)
                    logger.info(f"Removidas {len(keys)} chaves com padrão '{pattern}'")
                    return len(keys)
            except Exception as e:
                logger.error(f"Erro ao limpar padrão: {e}")
        else:
            # DatabaseCache: simula busca por padrão com chaves conhecidas
            common_suffixes = ["list", "detail", "stats", "popular", "summary"]
            keys_to_delete = [f"{pattern}:{suffix}" for suffix in common_suffixes]

            # Adiciona algumas variações com IDs
            for i in range(1, 11):
                keys_to_delete.append(f"{pattern}:detail:{i}")

            existing_keys = []
            for key in keys_to_delete:
                if self.cache.get(key) is not None:
                    existing_keys.append(key)

            if existing_keys:
                self.cache.delete_many(existing_keys)
                logger.info(
                    f"Removidas {len(existing_keys)} chaves com padrão '{pattern}' (DatabaseCache)"
                )
                return len(existing_keys)

        return 0

    def invalidate_pattern(self, pattern: str):
        """Invalida todas as chaves que correspondem ao padrão"""
        return self.clear_pattern(pattern)

    def get_cache_stats(self) -> dict:
        """Obtém estatísticas do cache"""
        stats = {
            "backend_info": self.get_backend_info(),
            "total_keys": 0,
        }

        if self.is_redis_backend() and self.redis_client:
            try:
                stats["total_keys"] = self.redis_client.dbsize()

                # Estatísticas por padrão
                patterns = ["barbershop", "service", "appointment", "user", "review"]
                for pattern in patterns:
                    keys = self.get_keys_by_pattern(pattern)
                    stats[f"{pattern}_keys"] = len(keys)

            except Exception as e:
                logger.error(f"Erro ao obter estatísticas: {e}")

        return stats

    def health_check(self) -> tuple[bool, str]:
        """Verifica se o cache está funcionando corretamente"""
        try:
            test_key = "health_check_test"
            test_value = {"timestamp": "2024-09-24", "status": "ok"}

            # Teste básico set/get
            self.cache.set(test_key, test_value, 10)
            result = self.cache.get(test_key)

            if result != test_value:
                return False, "Cache set/get failed"

            # Teste específico para Redis
            if self.is_redis_backend() and self.redis_client:
                self.redis_client.ping()
                return True, "Redis cache is healthy"
            else:
                return True, "Database cache is healthy"

        except Exception as e:
            error_msg = f"Cache health check failed: {e}"
            logger.error(error_msg)
            return False, error_msg

    def invalidate_related_cache(
        self, model_name: str, instance_id: Optional[int] = None
    ):
        """
        Invalida cache relacionado a um modelo específico

        Args:
            model_name: Nome do modelo (barbershop, service, etc.)
            instance_id: ID da instância específica (opcional)
        """
        patterns_to_invalidate = []

        if model_name == "barbershop":
            patterns_to_invalidate.extend(
                [
                    CacheKeys.BARBERSHOP_PREFIX,
                    CacheKeys.SERVICE_PREFIX,  # Serviços podem ser afetados
                    CacheKeys.APPOINTMENT_PREFIX,  # Slots disponíveis podem mudar
                ]
            )

        elif model_name == "service":
            patterns_to_invalidate.extend(
                [
                    CacheKeys.SERVICE_PREFIX,
                    CacheKeys.BARBERSHOP_PREFIX,  # Lista de barbearias pode mostrar serviços
                    CacheKeys.APPOINTMENT_PREFIX,  # Slots podem mudar
                ]
            )

        elif model_name == "appointment":
            patterns_to_invalidate.extend(
                [
                    CacheKeys.APPOINTMENT_PREFIX,
                    CacheKeys.BARBERSHOP_PREFIX,  # Stats podem mudar
                ]
            )

        elif model_name == "review":
            patterns_to_invalidate.extend(
                [
                    CacheKeys.REVIEW_PREFIX,
                    CacheKeys.BARBERSHOP_PREFIX,  # Avaliações afetam barbearias
                ]
            )

        elif model_name == "user":
            patterns_to_invalidate.extend(
                [
                    CacheKeys.USER_PREFIX,
                ]
            )

        # Invalida todos os padrões relacionados
        for pattern in patterns_to_invalidate:
            self.invalidate_pattern(pattern)

        # Se há ID específico, invalida cache desse item
        if instance_id:
            specific_keys = [
                f"{pattern}:detail:{instance_id}" for pattern in patterns_to_invalidate
            ]
            self.cache.delete_many(specific_keys)


def cache_response(
    ttl_type: str = "MEDIUM",
    cache_name: str = "default",
    key_prefix: str = "",
    vary_on_user: bool = False,
    vary_on_params: Optional[list] = None,
):
    """
    Decorator para cache de responses de views

    Args:
        ttl_type: Tipo de TTL (SHORT, MEDIUM, LONG, LISTING)
        cache_name: Nome do cache a ser usado
        key_prefix: Prefixo para a chave do cache
        vary_on_user: Se deve variar o cache por usuário
        vary_on_params: Lista de parâmetros da request para incluir na chave
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            cache_manager = CacheManager(cache_name)

            # Constrói chave do cache
            key_parts = [key_prefix] if key_prefix else []

            # Adiciona usuário se necessário
            if (
                vary_on_user
                and hasattr(request, "user")
                and request.user.is_authenticated
            ):
                key_parts.append(f"user:{request.user.id}")

            # Adiciona parâmetros específicos
            if vary_on_params:
                for param in vary_on_params:
                    value = request.GET.get(param) or request.POST.get(param)
                    if value:
                        key_parts.append(f"{param}:{value}")

            # Adiciona argumentos da URL
            for i, arg in enumerate(args):
                key_parts.append(f"arg{i}:{arg}")

            # Adiciona kwargs da URL
            for key, value in kwargs.items():
                key_parts.append(f"{key}:{value}")

            cache_key = ":".join(key_parts)

            # Tenta buscar do cache
            cached_response = cache_manager.cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # Executa a view e cachea o resultado
            response = view_func(request, *args, **kwargs)
            ttl = cache_manager.get_ttl(ttl_type)
            cache_manager.cache.set(cache_key, response, ttl)

            return response

        return wrapper

    return decorator


# Instância global do cache manager
cache_manager = CacheManager()
