"""
Configurações avançadas recomendadas para SPECTACULAR_SETTINGS

Adicione estas melhorias ao seu config/settings.py
"""

# Configurações avançadas para drf-spectacular
SPECTACULAR_SETTINGS = {
    # === INFORMAÇÕES BÁSICAS ===
    "TITLE": "Barbershop Management API",
    "DESCRIPTION": """
    # API para Gerenciamento de Barbearias
    
    Esta API REST completa oferece funcionalidades para:
    
    ## 🏪 Gestão de Barbearias
    - Cadastro e gerenciamento de estabelecimentos
    - Controle de serviços oferecidos
    - Gestão de barbeiros e funcionários
    
    ## 📅 Sistema de Agendamentos
    - Agendamento online de serviços
    - Consulta de horários disponíveis
    - Gerenciamento de agenda dos barbeiros
    
    ## 💰 Processamento de Pagamentos
    - Integração com gateways de pagamento
    - Controle financeiro e relatórios
    - Histórico de transações
    
    ## ⭐ Sistema de Avaliações
    - Reviews e ratings de clientes
    - Análise de satisfação
    - Ranking de barbeiros e serviços
    
    ## 🔐 Autenticação e Segurança
    - JWT Authentication
    - Controle de permissões por papel
    - Rate limiting e throttling
    - Cache inteligente para performance
    
    ## 📱 Features Mobile-Ready
    - API otimizada para aplicações móveis
    - Notificações push
    - Sincronização offline básica
    
    ---
    
    ### Versioning
    A API usa versionamento por URL path (`/api/v1/`). 
    Versões futuras manterão compatibilidade backwards quando possível.
    
    ### Rate Limiting
    - **Usuários autenticados**: 500 req/hora
    - **Usuários anônimos**: 50 req/hora
    - **Operações críticas**: Limits específicos por endpoint
    
    ### Caching
    - Cache automático em listagens (15 minutos)
    - Cache de horários disponíveis (5 minutos)
    - Invalidação inteligente em modificações
    """,
    "VERSION": "1.0.0",
    "CONTACT": {
        "name": "API Support Team",
        "email": "api-support@barbershop.com",
        "url": "https://barbershop.com/support",
    },
    "LICENSE": {"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    "EXTERNAL_DOCS": {
        "description": "Documentação adicional",
        "url": "https://docs.barbershop.com",
    },
    # === CONFIGURAÇÕES DE SERVIDOR ===
    "SERVERS": [
        {
            "url": "http://127.0.0.1:8000",
            "description": "Servidor de Desenvolvimento",
            "variables": {
                "port": {
                    "default": "8000",
                    "description": "Porta do servidor de desenvolvimento",
                }
            },
        },
        {
            "url": "https://api-staging.barbershop.com",
            "description": "Servidor de Staging/Homologação",
        },
        {"url": "https://api.barbershop.com", "description": "Servidor de Produção"},
    ],
    # === CONFIGURAÇÕES DE INTERFACE ===
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "defaultModelRendering": "model",
        "displayRequestDuration": True,
        "docExpansion": "none",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
        "requestSnippetsEnabled": True,
        "requestSnippets": {
            "generators": {
                "curl_bash": {"title": "cURL (bash)"},
                "curl_powershell": {"title": "cURL (PowerShell)"},
                "curl_cmd": {"title": "cURL (CMD)"},
                "javascript_fetch": {"title": "JavaScript (fetch)"},
                "javascript_xhr": {"title": "JavaScript (XHR)"},
                "python_requests": {"title": "Python (requests)"},
                "php_curl": {"title": "PHP (cURL)"},
                "java_okhttp": {"title": "Java (OkHttp)"},
            },
            "defaultExpanded": False,
            "languages": None,  # Null = all languages
        },
    },
    # === CONFIGURAÇÕES DE SCHEMA ===
    "SCHEMA_COERCE_PATH_PK": True,
    "SCHEMA_PATH_PREFIX": "/api/v1/",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "SERVE_INCLUDE_SCHEMA": False,
    # === CONFIGURAÇÕES DE COMPONENTES ===
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    "COMPONENT_SPLIT_PATCH": True,
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token obtido através do endpoint de login",
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API Key para integração de sistemas (opcional)",
            },
        }
    },
    # === CONFIGURAÇÕES DE ENUMS ===
    "ENUM_GENERATE_CHOICE_DESCRIPTION": True,
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": True,
    "ENUM_NAME_OVERRIDES": {
        "apps.appointment.models.Appointment.Status": "AppointmentStatusEnum",
        "apps.payment.models.Payment.Status": "PaymentStatusEnum",
        "apps.payment.models.Payment.Method": "PaymentMethodEnum",
        "apps.review.models.Review.RATING_CHOICES": "ReviewRatingEnum",
        "apps.user.models.User.USER_TYPE_CHOICES": "UserTypeEnum",
    },
    # === CONFIGURAÇÕES DE ORDENAÇÃO ===
    "SORT_OPERATIONS": True,
    "SORT_OPERATION_PARAMETERS": True,
    # === TAGS ORGANIZADAS ===
    "TAGS": [
        {
            "name": "authentication",
            "description": """
            ## 🔐 Autenticação e Autorização
            
            Endpoints para gerenciar autenticação JWT, login, logout, 
            registro de usuários e recuperação de senha.
            
            **Fluxo de Autenticação:**
            1. Registre-se ou faça login
            2. Receba o token JWT
            3. Use o token no header: `Authorization: Bearer <token>`
            """,
            "externalDocs": {
                "description": "Documentação sobre JWT",
                "url": "https://jwt.io/introduction/",
            },
        },
        {
            "name": "users",
            "description": """
            ## 👥 Gerenciamento de Usuários
            
            Operações relacionadas ao perfil do usuário, preferências
            e gerenciamento de conta.
            """,
        },
        {
            "name": "barbershops",
            "description": """
            ## 🏪 Gestão de Barbearias
            
            CRUD completo para barbearias, incluindo:
            - Cadastro e edição de estabelecimentos
            - Consulta com filtros avançados
            - Estatísticas e relatórios
            - Upload de imagens/logo
            """,
        },
        {
            "name": "services",
            "description": """
            ## ✂️ Serviços Oferecidos
            
            Gerenciamento dos serviços disponíveis em cada barbearia:
            - Cortes, barbas, tratamentos
            - Preços e duração
            - Disponibilidade
            """,
        },
        {
            "name": "appointments",
            "description": """
            ## 📅 Sistema de Agendamentos
            
            Funcionalidades para agendamento de serviços:
            - Consulta de horários disponíveis
            - Criação e gerenciamento de agendamentos
            - Confirmação e cancelamento
            - Histórico de agendamentos
            """,
        },
        {
            "name": "payments",
            "description": """
            ## 💰 Processamento de Pagamentos
            
            Sistema financeiro integrado:
            - Múltiplas formas de pagamento
            - Controle de transações
            - Relatórios financeiros
            - Reembolsos e estornos
            """,
        },
        {
            "name": "reviews",
            "description": """
            ## ⭐ Sistema de Avaliações
            
            Reviews e ratings dos clientes:
            - Avaliações de serviços e barbeiros
            - Sistema de estrelas (1-5)
            - Comentários e feedback
            - Estatísticas de satisfação
            """,
        },
    ],
    # === CONFIGURAÇÕES AVANÇADAS ===
    "DISABLE_ERRORS_AND_WARNINGS": False,
    "PREPROCESSING_HOOKS": [
        # Adicionar hooks personalizados aqui se necessário
    ],
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
    ],
    # === CONFIGURAÇÕES DE AUTENTICAÇÃO ===
    "SECURITY": [{"BearerAuth": []}],
    # === CONFIGURAÇÕES PERSONALIZADAS ===
    "CUSTOM_SETTINGS": {
        "api_version": "v1",
        "supported_languages": ["pt-BR", "en-US"],
        "default_language": "pt-BR",
        "timezone": "America/Sao_Paulo",
        "pagination": {"default_page_size": 10, "max_page_size": 100},
    },
}
