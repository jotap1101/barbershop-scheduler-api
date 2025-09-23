"""
Cache invalidation mixins para ViewSets Django REST Framework

Estes mixins automaticamente invalidam cache quando dados são modificados
"""

from typing import Any, Dict, Optional
from django.db import models
from rest_framework.response import Response
from rest_framework import status
from .cache_utils import cache_manager


class CacheInvalidationMixin:
    """
    Mixin que adiciona invalidação automática de cache em operações CRUD
    """

    # Nome do modelo para invalidação (deve ser definido na view)
    cache_model_name: Optional[str] = None

    # Padrões adicionais de cache para invalidar
    additional_cache_patterns: list = []

    def get_cache_model_name(self) -> str:
        """Retorna o nome do modelo para invalidação de cache"""
        if self.cache_model_name:
            return self.cache_model_name

        # Tenta inferir do queryset/serializer
        if hasattr(self, "queryset") and self.queryset is not None:
            return self.queryset.model._meta.model_name

        if hasattr(self, "serializer_class") and self.serializer_class:
            model = getattr(self.serializer_class.Meta, "model", None)
            if model:
                return model._meta.model_name

        return "unknown"

    def invalidate_cache(self, instance: Optional[models.Model] = None):
        """Invalida cache relacionado ao modelo"""
        model_name = self.get_cache_model_name()
        instance_id = getattr(instance, "id", None) if instance else None

        # Invalida cache do modelo principal
        cache_manager.invalidate_related_cache(model_name, instance_id)

        # Invalida padrões adicionais
        for pattern in self.additional_cache_patterns:
            cache_manager.invalidate_pattern(pattern)

    def perform_create(self, serializer):
        """Override para invalidar cache após criação"""
        instance = serializer.save()
        self.invalidate_cache(instance)
        return instance

    def perform_update(self, serializer):
        """Override para invalidar cache após atualização"""
        instance = serializer.save()
        self.invalidate_cache(instance)
        return instance

    def perform_destroy(self, instance):
        """Override para invalidar cache após exclusão"""
        # Captura ID antes de deletar
        instance_id = instance.id
        model_name = self.get_cache_model_name()

        # Deleta o objeto
        instance.delete()

        # Invalida cache usando ID capturado
        cache_manager.invalidate_related_cache(model_name, instance_id)

        # Invalida padrões adicionais
        for pattern in self.additional_cache_patterns:
            cache_manager.invalidate_pattern(pattern)


class ListCacheMixin:
    """
    Mixin para cache de listagens com parâmetros de filtro, busca e paginação
    """

    # TTL para cache de listagens
    cache_ttl_type: str = "LISTING"

    # Prefixo para chaves de cache
    cache_key_prefix: str = ""

    # Se deve variar cache por usuário
    cache_vary_on_user: bool = False

    # Parâmetros de query para incluir na chave de cache
    cache_vary_on_params: list = [
        "page",
        "page_size",
        "ordering",
        "search",
        "filter",
        "limit",
        "offset",
    ]

    def get_cache_key_prefix(self) -> str:
        """Retorna prefixo para chave de cache"""
        if self.cache_key_prefix:
            return self.cache_key_prefix

        # Usa nome da view ou modelo
        if hasattr(self, "__class__"):
            return self.__class__.__name__.lower().replace("viewset", "")

        return "list"

    def generate_list_cache_key(self) -> str:
        """Gera chave de cache para a listagem atual"""
        prefix = self.get_cache_key_prefix()

        # Coleta parâmetros relevantes
        cache_params = {}

        # Adiciona usuário se necessário
        if (
            self.cache_vary_on_user
            and hasattr(self.request, "user")
            and self.request.user.is_authenticated
        ):
            cache_params["user"] = self.request.user.id

        # Adiciona parâmetros de query
        for param in self.cache_vary_on_params:
            value = self.request.query_params.get(param)
            if value:
                cache_params[param] = value

        return cache_manager.generate_cache_key(prefix, **cache_params)

    def get_cached_list(self):
        """Busca listagem do cache"""
        cache_key = self.generate_list_cache_key()
        return cache_manager.cache.get(cache_key)

    def set_cached_list(self, data: Any):
        """Armazena listagem no cache"""
        cache_key = self.generate_list_cache_key()
        ttl = cache_manager.get_ttl(self.cache_ttl_type)
        cache_manager.cache.set(cache_key, data, ttl)

    def list(self, request, *args, **kwargs):
        """Override do método list com cache"""
        # Tenta buscar do cache primeiro
        cached_data = self.get_cached_list()
        if cached_data is not None:
            return Response(cached_data)

        # Se não está em cache, executa listagem normal
        response = super().list(request, *args, **kwargs)

        # Cachea a resposta se foi bem-sucedida
        if response.status_code == status.HTTP_200_OK:
            self.set_cached_list(response.data)

        return response


class DetailCacheMixin:
    """
    Mixin para cache de detalhes de objetos individuais
    """

    # TTL para cache de detalhes
    cache_ttl_type: str = "MEDIUM"

    # Prefixo para chaves de cache
    cache_key_prefix: str = ""

    def get_cache_key_prefix(self) -> str:
        """Retorna prefixo para chave de cache"""
        if self.cache_key_prefix:
            return self.cache_key_prefix

        # Usa nome da view ou modelo
        if hasattr(self, "__class__"):
            return self.__class__.__name__.lower().replace("viewset", "")

        return "detail"

    def generate_detail_cache_key(self, obj_id: Any) -> str:
        """Gera chave de cache para o objeto específico"""
        prefix = self.get_cache_key_prefix()
        return cache_manager.generate_cache_key(f"{prefix}:detail", id=obj_id)

    def get_cached_detail(self, obj_id: Any):
        """Busca detalhe do cache"""
        cache_key = self.generate_detail_cache_key(obj_id)
        return cache_manager.cache.get(cache_key)

    def set_cached_detail(self, obj_id: Any, data: Any):
        """Armazena detalhe no cache"""
        cache_key = self.generate_detail_cache_key(obj_id)
        ttl = cache_manager.get_ttl(self.cache_ttl_type)
        cache_manager.cache.set(cache_key, data, ttl)

    def retrieve(self, request, *args, **kwargs):
        """Override do método retrieve com cache"""
        # Obtém ID do objeto
        obj_id = kwargs.get(self.lookup_field, kwargs.get("pk"))

        # Tenta buscar do cache primeiro
        cached_data = self.get_cached_detail(obj_id)
        if cached_data is not None:
            return Response(cached_data)

        # Se não está em cache, executa retrieve normal
        response = super().retrieve(request, *args, **kwargs)

        # Cachea a resposta se foi bem-sucedida
        if response.status_code == status.HTTP_200_OK:
            self.set_cached_detail(obj_id, response.data)

        return response


class CompleteCacheMixin(CacheInvalidationMixin, ListCacheMixin, DetailCacheMixin):
    """
    Mixin completo que combina invalidação automática com cache de listagens e detalhes

    Este mixin oferece:
    - Cache automático para list() e retrieve()
    - Invalidação automática em create/update/delete
    - Configuração flexível de TTL e chaves de cache
    """

    pass
