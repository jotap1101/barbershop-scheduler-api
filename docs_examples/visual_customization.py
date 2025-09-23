"""
Customização visual avançada para drf-spectacular

Templates e estilos personalizados para a documentação
"""

# === TEMPLATE PERSONALIZADO PARA SWAGGER UI ===
SWAGGER_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Barbershop API Documentation</title>
    <link rel="stylesheet" type="text/css" href="{% static 'css/swagger-custom.css' %}" />
    <link rel="icon" type="image/png" href="{% static 'img/favicon.png' %}" sizes="32x32" />
    <style>
        /* CSS personalizado inline */
        .swagger-ui .topbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-bottom: 3px solid #5a67d8;
        }
        
        .swagger-ui .topbar .download-url-wrapper .select-label {
            color: white;
        }
        
        .swagger-ui .info .title {
            color: #2d3748;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .swagger-ui .info .description {
            color: #4a5568;
            line-height: 1.6;
        }
        
        /* Customiza tags */
        .swagger-ui .opblock.opblock-post {
            border-color: #38a169;
        }
        
        .swagger-ui .opblock.opblock-get {
            border-color: #3182ce;
        }
        
        .swagger-ui .opblock.opblock-put {
            border-color: #d69e2e;
        }
        
        .swagger-ui .opblock.opblock-delete {
            border-color: #e53e3e;
        }
        
        /* Logo personalizado */
        .swagger-ui .topbar .topbar-wrapper:before {
            content: '';
            background-image: url('{% static "img/logo.png" %}');
            background-size: contain;
            background-repeat: no-repeat;
            width: 120px;
            height: 40px;
            display: inline-block;
            margin-right: 20px;
        }
        
        /* Customiza botões */
        .swagger-ui .btn {
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .swagger-ui .btn.authorize {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            border-color: #38a169;
        }
        
        .swagger-ui .btn.authorize:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(56, 161, 105, 0.3);
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    
    <script>
        // Configuração personalizada do Swagger UI
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "{{ schema_url }}",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                
                // Customizações específicas
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                docExpansion: "list",
                filter: true,
                showRequestHeaders: true,
                showCommonExtensions: true,
                
                // Plugin personalizado para adicionar informações extras
                requestInterceptor: function(request) {
                    // Adiciona headers personalizados se necessário
                    request.headers['X-Requested-With'] = 'SwaggerUI';
                    return request;
                },
                
                responseInterceptor: function(response) {
                    // Log de respostas para debug
                    if (response.status >= 400) {
                        console.warn('API Error:', response);
                    }
                    return response;
                },
                
                // Customiza a exibição de operações
                operationsSorter: "alpha",
                tagsSorter: "alpha"
            });
            
            // Adiciona funcionalidades extras após carregamento
            ui.preauthorizeApiKey('BearerAuth', 'Bearer your-jwt-token-here');
            
            // Analytics (se necessário)
            if (typeof gtag !== 'undefined') {
                gtag('event', 'page_view', {
                    page_title: 'API Documentation',
                    page_location: window.location.href
                });
            }
        }
    </script>
</body>
</html>
"""

# === CSS PERSONALIZADO ===
CUSTOM_CSS = """
/* swagger-custom.css */

/* Tema escuro opcional */
@media (prefers-color-scheme: dark) {
    .swagger-ui {
        background-color: #1a202c;
        color: #e2e8f0;
    }
    
    .swagger-ui .info .title {
        color: #f7fafc;
    }
    
    .swagger-ui .info .description {
        color: #cbd5e0;
    }
    
    .swagger-ui .scheme-container {
        background-color: #2d3748;
        border-color: #4a5568;
    }
}

/* Responsividade mobile */
@media (max-width: 768px) {
    .swagger-ui .topbar .topbar-wrapper:before {
        width: 80px;
        height: 30px;
        margin-right: 10px;
    }
    
    .swagger-ui .info .title {
        font-size: 24px;
    }
    
    .swagger-ui .wrapper {
        padding: 0 10px;
    }
}

/* Animações suaves */
.swagger-ui .opblock {
    transition: all 0.3s ease;
}

.swagger-ui .opblock:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Melhor legibilidade dos códigos */
.swagger-ui .highlight-code {
    background-color: #f7fafc;
    border-left: 4px solid #4299e1;
    padding: 16px;
    border-radius: 6px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

/* Status codes coloridos */
.swagger-ui .response-col_status {
    font-weight: bold;
}

.swagger-ui .response-col_status[data-code^="2"] {
    color: #38a169;
}

.swagger-ui .response-col_status[data-code^="4"] {
    color: #d69e2e;
}

.swagger-ui .response-col_status[data-code^="5"] {
    color: #e53e3e;
}

/* Badges personalizados para tags */
.swagger-ui .opblock-tag {
    position: relative;
}

.swagger-ui .opblock-tag[data-tag="authentication"]:before {
    content: "🔐";
    margin-right: 8px;
}

.swagger-ui .opblock-tag[data-tag="barbershops"]:before {
    content: "🏪";
    margin-right: 8px;
}

.swagger-ui .opblock-tag[data-tag="appointments"]:before {
    content: "📅";
    margin-right: 8px;
}

.swagger-ui .opblock-tag[data-tag="payments"]:before {
    content: "💰";
    margin-right: 8px;
}

.swagger-ui .opblock-tag[data-tag="reviews"]:before {
    content: "⭐";
    margin-right: 8px;
}
"""

# === CONFIGURAÇÕES PARA ADICIONAR AO SETTINGS.PY ===
SPECTACULAR_CUSTOM_SETTINGS = {
    # Adicione ao seu SPECTACULAR_SETTINGS existente
    # Templates personalizados
    "SWAGGER_UI_SETTINGS": {
        # ... suas configurações existentes ...
        # Configurações de interface personalizadas
        "displayOperationId": True,
        "displayRequestDuration": True,
        "defaultModelRendering": "model",
        "defaultModelExpandDepth": 2,
        "defaultModelsExpandDepth": 1,
        "docExpansion": "list",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "useUnsafeMarkdown": False,
        # Personalização visual
        "supportedSubmitMethods": ["get", "post", "put", "delete", "patch"],
        "validatorUrl": None,  # Desabilita validação externa
        # Configurações de autenticação
        "persistAuthorization": True,
        "oauth2RedirectUrl": None,
        # Layout customizado
        "layout": "StandaloneLayout",
        "deepLinking": True,
        "displayOperationId": False,
        "showMutatedRequest": True,
        # Customizações específicas da API
        "tryItOutEnabled": True,
        "requestSnippetsEnabled": True,
        "syntaxHighlight": {"activate": True, "theme": "agate"},
    },
    # Favicon personalizado
    "SWAGGER_UI_FAVICON_HREF": "https://yourdomain.com/favicon.ico",
    # URL do logo
    "CUSTOM_LOGO_URL": "https://yourdomain.com/logo.png",
    # Configurações do ReDoc (alternativa ao Swagger UI)
    "REDOC_SETTINGS": {
        "nativeScrollbars": False,
        "theme": {
            "colors": {"primary": {"main": "#667eea"}},
            "typography": {
                "fontSize": "14px",
                "lineHeight": "1.5em",
                "code": {
                    "fontSize": "13px",
                    "fontFamily": "Monaco, Consolas, 'Lucida Console', monospace",
                },
                "headings": {
                    "fontFamily": "Montserrat, sans-serif",
                    "fontWeight": "600",
                },
            },
            "sidebar": {"width": "300px", "backgroundColor": "#f8f9fa"},
        },
        "hideDownloadButton": False,
        "expandResponses": "200,201",
        "requiredPropsFirst": True,
        "sortPropsAlphabetically": True,
        "showExtensions": True,
        "pathInMiddlePanel": True,
        "scrollYOffset": 0,
    },
}

# === EXEMPLO DE CONFIGURAÇÃO NO PROJETO ===
"""
Para implementar as customizações visuais:

1. Crie os diretórios:
   static/css/
   static/img/
   templates/

2. Adicione os arquivos:
   - static/css/swagger-custom.css (com o CSS acima)
   - static/img/logo.png (seu logo)
   - static/img/favicon.png (seu favicon)

3. No settings.py, adicione:
   STATICFILES_DIRS = [
       BASE_DIR / "static",
   ]

4. Atualize seu SPECTACULAR_SETTINGS com as configurações personalizadas

5. Opcional: Crie template personalizado em templates/swagger-ui.html
"""
