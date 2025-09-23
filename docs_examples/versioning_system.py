"""
Sistema de versionamento de schema para drf-spectacular

Implementação de versionamento mais robusto
"""

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import AutoSchema
from rest_framework import versioning
from rest_framework.request import Request


class CustomAutoSchema(AutoSchema):
    """
    Schema personalizado para adicionar informações de versionamento
    """

    def get_operation_id(self):
        """Adiciona versão no operation ID"""
        operation_id = super().get_operation_id()
        if hasattr(self.request, "version"):
            return f"{self.request.version}_{operation_id}"
        return operation_id

    def get_tags(self):
        """Adiciona tags específicas por versão"""
        tags = super().get_tags()
        if hasattr(self.request, "version") and self.request.version:
            # Adiciona tag de versão
            tags.append(f"v{self.request.version}")
        return tags

    def get_description(self):
        """Adiciona informação de versão na descrição"""
        description = super().get_description()
        if hasattr(self.request, "version"):
            version_note = f"\n\n**API Version:** {self.request.version}"
            description = (description or "") + version_note
        return description


class APIVersioningScheme(versioning.NamespaceVersioning):
    """
    Esquema de versionamento personalizado com melhor documentação
    """

    allowed_versions = ["v1", "v2"]  # Versões suportadas
    default_version = "v1"
    version_param = "version"

    def determine_version(self, request, **kwargs):
        """
        Determina versão da API baseado na URL
        """
        version = super().determine_version(request, **kwargs)

        # Adiciona informações de versão ao request para uso no schema
        if version:
            request.api_version_info = {
                "version": version,
                "is_latest": version == max(self.allowed_versions),
                "deprecated": self._is_version_deprecated(version),
            }

        return version

    def _is_version_deprecated(self, version):
        """Verifica se uma versão está deprecated"""
        deprecated_versions = []  # Adicione versões deprecated aqui
        return version in deprecated_versions


# Decorators personalizados para documentação de versionamento
def versioned_endpoint(
    version_added=None, version_deprecated=None, version_removed=None
):
    """
    Decorator para documentar versionamento de endpoints

    Args:
        version_added: Versão em que o endpoint foi adicionado
        version_deprecated: Versão em que foi marcado como deprecated
        version_removed: Versão em que será removido
    """

    def decorator(func):
        # Adiciona informações de versionamento ao docstring
        version_info = []

        if version_added:
            version_info.append(f"**Adicionado na versão:** {version_added}")

        if version_deprecated:
            version_info.append(f"**⚠️ DEPRECATED desde:** {version_deprecated}")

        if version_removed:
            version_info.append(f"**🚫 Será removido na versão:** {version_removed}")

        if version_info:
            version_note = "\n\n### Informações de Versionamento\n" + "\n".join(
                version_info
            )
            if hasattr(func, "__doc__") and func.__doc__:
                func.__doc__ += version_note
            else:
                func.__doc__ = version_note

        return func

    return decorator


# Exemplos de uso nos ViewSets
class VersionedBarbershopViewSet:
    """
    Exemplo de como aplicar versionamento aos ViewSets
    """

    @extend_schema(
        summary="Listar barbearias",
        description="""
        Lista todas as barbearias cadastradas.
        
        ### Mudanças por Versão:
        - **v1.0**: Implementação inicial
        - **v1.1**: Adicionado campo `total_revenue`
        - **v2.0**: Mudança na estrutura de resposta (breaking change)
        """,
    )
    @versioned_endpoint(version_added="v1.0")
    def list(self, request):
        pass

    @extend_schema(
        summary="Estatísticas avançadas",
        description="Retorna estatísticas detalhadas da barbearia",
    )
    @versioned_endpoint(version_added="v1.1", version_deprecated="v2.0")
    def advanced_stats(self, request):
        pass


# Configurações para urls.py com versionamento
"""
# Exemplo de configuração no urls.py

from django.urls import path, include
from .views import BarbershopViewSet

# URLs versionadas
urlpatterns = [
    # Versão 1
    path('api/v1/', include([
        path('barbershops/', BarbershopViewSet.as_view({
            'get': 'list_v1',
            'post': 'create'
        })),
    ])),
    
    # Versão 2 (com mudanças breaking)
    path('api/v2/', include([
        path('barbershops/', BarbershopViewSet.as_view({
            'get': 'list_v2',
            'post': 'create'
        })),
    ])),
]
"""

# Schema customizado para documentação de mudanças entre versões
VERSION_CHANGELOG = {
    "v1.0": {
        "release_date": "2024-01-01",
        "changes": [
            "🎉 Lançamento inicial da API",
            "✨ CRUD completo para barbearias",
            "✨ Sistema de agendamentos",
            "✨ Autenticação JWT",
        ],
    },
    "v1.1": {
        "release_date": "2024-02-01",
        "changes": [
            "✨ Adicionado campo `total_revenue` nas barbearias",
            "✨ Endpoint de estatísticas avançadas",
            "🐛 Correções de validação em agendamentos",
            "⚡ Melhorias de performance com cache",
        ],
    },
    "v2.0": {
        "release_date": "2024-06-01",
        "changes": [
            "💥 BREAKING: Mudança na estrutura de resposta das listagens",
            "💥 BREAKING: Remoção de campos deprecated",
            "✨ Nova API de notificações",
            "✨ Sistema de fidelidade",
            "⚠️ Deprecação do endpoint de estatísticas antigas",
        ],
        "migration_guide": """
        ### Guia de Migração v1 -> v2
        
        1. **Listagens**: Agora retornam estrutura aninhada
        2. **Campos removidos**: `old_field_name` -> usar `new_field_name`
        3. **Novos headers obrigatórios**: `X-API-Version: v2`
        """,
    },
}
