"""
Cache utilities para a API Django REST Framework

Este módulo fornece utilitários para cache inteligente e invalidação
"""

from functools import wraps
from typing import Any, Callable, Optional, Union
from django.core.cache import cache, caches
from django.conf import settings
from django.http import HttpRequest
import hashlib
import json


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

    def invalidate_pattern(self, pattern: str):
        """Invalida todas as chaves que correspondem ao padrão"""
        # Para cache simples, removemos chaves específicas
        # Em produção, considere usar Redis com padrões
        keys_to_delete = []

        # Simula busca por padrão (limitação do cache database)
        # Em produção, use Redis para suporte completo a padrões
        common_keys = [
            f"{pattern}:list",
            f"{pattern}:detail",
            f"{pattern}:stats",
            f"{pattern}:popular",
        ]

        for key in common_keys:
            keys_to_delete.append(key)

        self.cache.delete_many(keys_to_delete)

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
