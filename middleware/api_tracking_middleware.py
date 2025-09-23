"""
API Usage Tracking Middleware para Sistema de Barbearia

Este middleware monitora e registra o uso das APIs, incluindo:
- Performance de endpoints
- Frequência de uso por usuário
- Detecção de padrões anômalos
- Métricas para otimização
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

        # Configurações do tracking
        self.track_paths = ["/api/"]  # Paths para rastrear
        self.ignore_paths = [
            "/api/health/",  # Health checks
            "/api/docs/",  # Documentação
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
        Identifica endpoints críticos que precisam de log detalhado
        """
        critical_paths = [
            "/api/auth/",
            "/api/payment/",
            "/api/appointment/",
        ]

        return any(request.path.startswith(path) for path in critical_paths)

    def prepare_tracking_data(self, request, response, duration):
        """
        Prepara dados completos para tracking
        """
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
            "endpoint_category": self.categorize_endpoint(request.path),
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
        Categoriza endpoint para análise
        """
        if "/auth/" in path:
            return "authentication"
        elif "/appointment/" in path:
            return "appointment"
        elif "/payment/" in path:
            return "payment"
        elif "/barbershop/" in path:
            return "barbershop"
        elif "/review/" in path:
            return "review"
        elif "/user/" in path:
            return "user"
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
