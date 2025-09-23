"""
Sistema de Health Checks e Monitoring para documentação da API

Endpoints de monitoramento que devem ser documentados
"""

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connections
from django.core.cache import cache
from django.conf import settings
import time


@extend_schema(
    summary="Health Check da API",
    description="""
    ## Endpoint de Health Check
    
    Verifica a saúde geral da API e seus componentes principais:
    - Status da aplicação
    - Conectividade com banco de dados
    - Funcionalidade do cache
    - Tempo de resposta
    
    Este endpoint é usado para:
    - Monitoramento automático (ex: Kubernetes probes)
    - Dashboards de status
    - Alertas de sistema
    
    **Códigos de Status:**
    - `200`: Tudo funcionando normalmente
    - `503`: Algum componente com problemas
    """,
    tags=["monitoring"],
    responses={
        200: OpenApiResponse(
            description="API funcionando normalmente",
            examples=[
                OpenApiExample(
                    "Sistema saudável",
                    value={
                        "status": "healthy",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "version": "1.0.0",
                        "environment": "production",
                        "response_time_ms": 45,
                        "checks": {
                            "database": {"status": "healthy", "response_time_ms": 12},
                            "cache": {"status": "healthy", "response_time_ms": 3},
                            "storage": {"status": "healthy", "response_time_ms": 8},
                        },
                        "uptime_seconds": 86400,
                    },
                )
            ],
        ),
        503: OpenApiResponse(
            description="Problemas detectados no sistema",
            examples=[
                OpenApiExample(
                    "Sistema com problemas",
                    value={
                        "status": "unhealthy",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "version": "1.0.0",
                        "environment": "production",
                        "response_time_ms": 1200,
                        "checks": {
                            "database": {
                                "status": "unhealthy",
                                "error": "Connection timeout",
                                "response_time_ms": 5000,
                            },
                            "cache": {"status": "healthy", "response_time_ms": 3},
                            "storage": {
                                "status": "degraded",
                                "warning": "High latency",
                                "response_time_ms": 800,
                            },
                        },
                    },
                )
            ],
        ),
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Endpoint de health check da API"""
    start_time = time.time()

    # Verifica componentes
    checks = {
        "database": check_database(),
        "cache": check_cache(),
        "storage": check_storage(),
    }

    # Determina status geral
    is_healthy = all(
        check["status"] in ["healthy", "degraded"] for check in checks.values()
    )
    overall_status = "healthy" if is_healthy else "unhealthy"

    response_data = {
        "status": overall_status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": getattr(settings, "API_VERSION", "1.0.0"),
        "environment": getattr(settings, "ENVIRONMENT", "development"),
        "response_time_ms": int((time.time() - start_time) * 1000),
        "checks": checks,
    }

    status_code = (
        status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return Response(response_data, status=status_code)


@extend_schema(
    summary="Métricas da API",
    description="""
    ## Endpoint de Métricas
    
    Retorna métricas de uso e performance da API:
    - Número total de requests
    - Requests por endpoint
    - Tempo médio de resposta
    - Taxa de erro
    - Estatísticas de cache
    
    **Uso típico:**
    - Integração com ferramentas de monitoramento (Prometheus, Grafana)
    - Dashboards de analytics
    - Alertas baseados em métricas
    """,
    tags=["monitoring"],
    responses={
        200: OpenApiResponse(
            description="Métricas da API",
            examples=[
                OpenApiExample(
                    "Métricas de exemplo",
                    value={
                        "requests": {
                            "total": 150000,
                            "last_hour": 1250,
                            "last_24h": 28000,
                            "by_endpoint": {
                                "/api/v1/barbershops/": 45000,
                                "/api/v1/appointments/": 38000,
                                "/api/v1/auth/login/": 12000,
                            },
                        },
                        "response_times": {
                            "avg_ms": 120,
                            "p50_ms": 95,
                            "p95_ms": 280,
                            "p99_ms": 650,
                        },
                        "errors": {
                            "rate_percent": 2.1,
                            "total_4xx": 2800,
                            "total_5xx": 350,
                        },
                        "cache": {
                            "hit_rate_percent": 78.5,
                            "total_hits": 89000,
                            "total_misses": 24000,
                        },
                        "active_users": {"last_hour": 145, "last_24h": 2100},
                    },
                )
            ],
        )
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def metrics(request):
    """Endpoint de métricas da API"""
    # Implementação das métricas...
    pass


def check_database():
    """Verifica conectividade com banco de dados"""
    try:
        start_time = time.time()
        connection = connections["default"]
        connection.ensure_connection()

        # Testa uma query simples
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        response_time = int((time.time() - start_time) * 1000)

        return {"status": "healthy", "response_time_ms": response_time}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": int((time.time() - start_time) * 1000),
        }


def check_cache():
    """Verifica funcionalidade do cache"""
    try:
        start_time = time.time()

        # Testa set/get no cache
        test_key = "health_check_test"
        test_value = "test_value"

        cache.set(test_key, test_value, 30)
        retrieved_value = cache.get(test_key)

        if retrieved_value == test_value:
            cache.delete(test_key)  # Limpa o teste
            response_time = int((time.time() - start_time) * 1000)
            return {"status": "healthy", "response_time_ms": response_time}
        else:
            return {
                "status": "unhealthy",
                "error": "Cache not working properly",
                "response_time_ms": int((time.time() - start_time) * 1000),
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": int((time.time() - start_time) * 1000),
        }


def check_storage():
    """Verifica acesso ao sistema de arquivos/storage"""
    try:
        start_time = time.time()

        # Verifica se consegue escrever/ler um arquivo temporário
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("health_check_test")
            temp_file = f.name

        # Tenta ler o arquivo
        with open(temp_file, "r") as f:
            content = f.read()

        # Remove o arquivo
        os.unlink(temp_file)

        response_time = int((time.time() - start_time) * 1000)

        if content == "health_check_test":
            # Verifica se o tempo de resposta está muito alto (degraded)
            if response_time > 500:
                return {
                    "status": "degraded",
                    "warning": "High latency detected",
                    "response_time_ms": response_time,
                }
            else:
                return {"status": "healthy", "response_time_ms": response_time}
        else:
            return {
                "status": "unhealthy",
                "error": "Storage read/write failed",
                "response_time_ms": response_time,
            }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": int((time.time() - start_time) * 1000),
        }


# Configuração para urls.py
"""
# Adicione estas URLs no seu urls.py

from django.urls import path
from .monitoring import health_check, metrics

urlpatterns = [
    # ... suas URLs existentes ...
    
    # Endpoints de monitoramento
    path('health/', health_check, name='health-check'),
    path('metrics/', metrics, name='api-metrics'),
]
"""
