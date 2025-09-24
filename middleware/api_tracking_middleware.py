"""
API Usage Tracking Middleware para Sistema de Barbearia

Este middleware monitora e registra o uso das APIs, incluindo:
- Performance de endpoints
- Frequência de uso por usuário
- Detecção de padrões anômalos
- Métricas para otimização

Rotas monitoradas baseadas na estrutura real da aplicação:
- /api/v1/token/* - Autenticação JWT (obtain, refresh, verify, blacklist)
- /api/v1/users/* - Gestão de usuários (ViewSet completo)
- /api/v1/barbershops/* - Gestão de barbearias
- /api/v1/services/* - Gestão de serviços
- /api/v1/barbershop-customers/* - Gestão de clientes das barbearias
- /api/v1/appointments/* - Gestão de agendamentos
- /api/v1/barber-schedules/* - Gestão de horários dos barbeiros
- /api/v1/payments/* - Processamento de pagamentos
- /api/v1/reviews/* - Sistema de avaliações
- /api/schema/* - Documentação da API (drf-spectacular)

Rotas ignoradas:
- /api/schema/swagger-ui/ - Interface Swagger
- /api/schema/redoc/ - Interface ReDoc
- /api-auth/ - Interface de auth do DRF
- /admin/ - Admin do Django
- /static/ e /media/ - Arquivos estáticos
"""

import time
import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from datetime import datetime


# Configurar logger específico para API usage
api_usage_logger = logging.getLogger("api_usage")


class APIUsageTrackingMiddleware(MiddlewareMixin):
    """
    Middleware para rastreamento de uso da API com métricas detalhadas.

    Funcionalidades:
    - Mede tempo de resposta de cada endpoint
    - Registra IP, User-Agent e usuário
    - Identifica endpoints mais utilizados
    - Detecta possíveis abusos
    - Coleta métricas para otimização
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response

        # Configurações do tracking baseadas nas rotas reais
        self.track_paths = [
            "/api/v1/",  # API versão 1 (rotas principais)
            "/api/schema/",  # Schema da API
        ]

        self.ignore_paths = [
            "/api/schema/swagger-ui/",  # Interface Swagger
            "/api/schema/redoc/",  # Interface ReDoc
            "/api-auth/",  # DRF auth interface
            "/admin/",  # Admin do Django
            "/static/",  # Arquivos estáticos
            "/media/",  # Arquivos de mídia
        ]

        # Limites para alertas
        self.slow_request_threshold = 2.0  # segundos
        self.error_log_enabled = True

    def process_request(self, request):
        """
        Processamento no início da requisição
        """
        if self.should_track_request(request):
            # Marcar início do tempo
            request.api_start_time = time.time()
            request.api_start_datetime = datetime.now()

            # Extrair informações da requisição
            request.api_client_info = self.extract_client_info(request)

            # Log da requisição (apenas para endpoints críticos)
            if self.is_critical_endpoint(request):
                api_usage_logger.info(
                    f"REQUEST_START: {request.method} {request.path} - User: {request.user}"
                )

    def process_response(self, request, response):
        """
        Processamento no final da requisição
        """
        if hasattr(request, "api_start_time") and self.should_track_request(request):
            # Calcular métricas
            duration = time.time() - request.api_start_time

            # Preparar dados para log
            tracking_data = self.prepare_tracking_data(request, response, duration)

            # Registrar no log
            api_usage_logger.info(json.dumps(tracking_data))

            # Alertas para requisições lentas
            if duration > self.slow_request_threshold:
                api_usage_logger.warning(
                    f"SLOW_REQUEST: {request.path} took {duration:.3f}s"
                )

            # Log de erros HTTP
            if response.status_code >= 400 and self.error_log_enabled:
                error_data = {
                    "type": "API_ERROR",
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "user": self.get_user_identifier(request.user),
                    "ip": tracking_data["client_ip"],
                    "duration": duration,
                    "timestamp": tracking_data["timestamp"],
                }
                api_usage_logger.error(json.dumps(error_data))

        return response

    def process_exception(self, request, exception):
        """
        Processamento quando ocorre exceção
        """
        if hasattr(request, "api_start_time") and self.should_track_request(request):
            duration = time.time() - request.api_start_time

            exception_data = {
                "type": "API_EXCEPTION",
                "method": request.method,
                "path": request.path,
                "exception": str(exception),
                "exception_type": type(exception).__name__,
                "user": self.get_user_identifier(request.user),
                "ip": self.get_client_ip(request),
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
            }

            api_usage_logger.error(json.dumps(exception_data))

    def should_track_request(self, request):
        """
        Determina se a requisição deve ser rastreada
        """
        path = request.path

        # Verificar se está em paths ignorados
        for ignore_path in self.ignore_paths:
            if path.startswith(ignore_path):
                return False

        # Verificar se está em paths para rastrear
        for track_path in self.track_paths:
            if path.startswith(track_path):
                return True

        return False

    def is_critical_endpoint(self, request):
        """
        Identifica endpoints críticos que precisam de log detalhado baseados nas rotas reais
        """
        critical_paths = [
            "/api/v1/token/",  # Autenticação JWT (token obtain, refresh, verify, blacklist)
            "/api/v1/users/",  # Gestão de usuários
            "/api/v1/payments/",  # Processamento de pagamentos
            "/api/v1/appointments/",  # Agendamentos
            "/api/v1/barbershops/",  # Dados das barbearias
        ]

        return any(request.path.startswith(path) for path in critical_paths)

    def prepare_tracking_data(self, request, response, duration):
        """
        Prepara dados completos para tracking baseado nas rotas reais
        """
        endpoint_details = self.get_endpoint_details(request.path, request.method)

        return {
            "type": "API_REQUEST",
            "timestamp": request.api_start_datetime.isoformat(),
            "method": request.method,
            "path": request.path,
            "query_params": dict(request.GET),
            "status_code": response.status_code,
            "duration": round(duration, 3),
            "duration_ms": round(duration * 1000, 1),
            "user": self.get_user_identifier(request.user),
            "user_type": self.get_user_type(request.user),
            "client_ip": self.get_client_ip(request),
            "user_agent": self.get_user_agent(request),
            "content_length": response.get("Content-Length", 0),
            "endpoint_category": endpoint_details["category"],
            "endpoint_type": endpoint_details["endpoint_type"],
            "is_critical_endpoint": endpoint_details["is_critical"],
            "requires_auth": endpoint_details["requires_auth"],
            "is_mobile": self.is_mobile_request(request),
            "response_size_category": self.categorize_response_size(
                response.get("Content-Length", 0)
            ),
        }

    def extract_client_info(self, request):
        """
        Extrai informações detalhadas do cliente
        """
        return {
            "ip": self.get_client_ip(request),
            "user_agent": self.get_user_agent(request),
            "is_mobile": self.is_mobile_request(request),
            "referer": request.META.get("HTTP_REFERER", ""),
        }

    def get_client_ip(self, request):
        """
        Obtém IP real do cliente (considerando proxies)
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip

        return request.META.get("REMOTE_ADDR", "unknown")

    def get_user_agent(self, request):
        """
        Obtém User-Agent truncado para log
        """
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        return user_agent[:200] if user_agent else "unknown"

    def get_user_identifier(self, user):
        """
        Obtém identificador seguro do usuário
        """
        if isinstance(user, AnonymousUser):
            return "anonymous"

        return f"{user.username}#{user.id}" if user else "unknown"

    def get_user_type(self, user):
        """
        Categoriza tipo do usuário
        """
        if isinstance(user, AnonymousUser):
            return "anonymous"

        if not user:
            return "unknown"

        if user.is_superuser:
            return "superuser"
        elif user.is_staff:
            return "staff"
        else:
            return "customer"

    def is_mobile_request(self, request):
        """
        Detecta se é requisição de dispositivo móvel
        """
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        mobile_indicators = [
            "mobile",
            "android",
            "iphone",
            "ipad",
            "ios",
            "phone",
            "tablet",
        ]

        return any(indicator in user_agent for indicator in mobile_indicators)

    def categorize_endpoint(self, path):
        """
        Categoriza endpoint para análise baseado nas rotas reais da aplicação
        """
        # Rotas de autenticação JWT
        if "/token/" in path:
            return "authentication"
        # Rotas de usuários
        elif "/users/" in path:
            return "user_management"
        # Rotas de agendamentos
        elif "/appointments/" in path or "/barber-schedules/" in path:
            return "appointment"
        # Rotas de pagamentos
        elif "/payments/" in path:
            return "payment"
        # Rotas de barbearias e serviços
        elif (
            "/barbershops/" in path
            or "/services/" in path
            or "/barbershop-customers/" in path
        ):
            return "barbershop"
        # Rotas de avaliações
        elif "/reviews/" in path:
            return "review"
        # Rotas de documentação da API
        elif "/schema/" in path:
            return "api_documentation"
        # Interface de autenticação do DRF
        elif "/api-auth/" in path:
            return "drf_auth_interface"
        # Admin do Django
        elif "/admin/" in path:
            return "admin"
        else:
            return "other"

    def categorize_response_size(self, content_length):
        """
        Categoriza tamanho da resposta
        """
        try:
            size = int(content_length)
            if size < 1024:  # < 1KB
                return "small"
            elif size < 51200:  # < 50KB
                return "medium"
            elif size < 512000:  # < 500KB
                return "large"
            else:
                return "xlarge"
        except (ValueError, TypeError):
            return "unknown"

    def get_endpoint_details(self, path, method):
        """
        Fornece detalhes específicos do endpoint baseado nas rotas reais
        """
        endpoint_info = {
            "category": self.categorize_endpoint(path),
            "is_critical": False,
            "requires_auth": True,  # Por padrão, assumimos que precisa autenticação
            "endpoint_type": "unknown",
        }

        # Rotas de autenticação
        if "/token/" in path:
            endpoint_info.update(
                {
                    "is_critical": True,
                    "requires_auth": False if method == "POST" else True,
                    "endpoint_type": "auth_token",
                }
            )

        # Rotas de usuários (ViewSet completo)
        elif "/users/" in path:
            endpoint_info.update({"is_critical": True, "endpoint_type": "user_crud"})

        # Rotas de agendamentos
        elif "/appointments/" in path:
            endpoint_info.update(
                {"is_critical": True, "endpoint_type": "appointment_crud"}
            )
        elif "/barber-schedules/" in path:
            endpoint_info.update(
                {"is_critical": True, "endpoint_type": "schedule_crud"}
            )

        # Rotas de pagamentos
        elif "/payments/" in path:
            endpoint_info.update({"is_critical": True, "endpoint_type": "payment_crud"})

        # Rotas de barbearias
        elif "/barbershops/" in path:
            endpoint_info.update({"endpoint_type": "barbershop_crud"})
        elif "/services/" in path:
            endpoint_info.update({"endpoint_type": "service_crud"})
        elif "/barbershop-customers/" in path:
            endpoint_info.update({"endpoint_type": "customer_crud"})

        # Rotas de avaliações
        elif "/reviews/" in path:
            endpoint_info.update({"endpoint_type": "review_crud"})

        # Rotas de documentação (não precisam auth)
        elif "/schema/" in path:
            endpoint_info.update(
                {"requires_auth": False, "endpoint_type": "api_documentation"}
            )

        return endpoint_info
