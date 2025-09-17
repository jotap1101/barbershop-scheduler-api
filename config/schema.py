from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny

@extend_schema(
    tags=['API'],
    description='Download the API OpenAPI schema. This endpoint returns the complete API documentation in OpenAPI 3.0 format, '
                'which can be used to generate clients, view interactive documentation, and understand all available endpoints. '
                'The schema is public and does not require authentication.',
    summary='OpenAPI Schema',
    responses={
        200: {
            'description': 'OpenAPI 3.0 schema in JSON format',
            'content': {
                'application/json': {
                    'example': {
                        'openapi': '3.0.3',
                        'info': {
                            'title': 'Barbershop API',
                            'version': '1.0.0'
                        },
                        'paths': '...',
                        'components': '...'
                    }
                }
            }
        }
    }
)
class PublicSpectacularAPIView(SpectacularAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

@extend_schema(
    tags=['API'],
    description='Interactive Swagger UI interface to explore and test the API. '
                'Provides a graphical interface to view all endpoints, their parameters, request/response schemas, '
                'and allows making test requests directly from the browser.',
    summary='Swagger UI'
)
class PublicSpectacularSwaggerView(SpectacularSwaggerView):
    permission_classes = [AllowAny]
    authentication_classes = []

@extend_schema(
    tags=['API'],
    description='ReDoc interface for API documentation. '
                'Provides a clean and organized view of the documentation, '
                'ideal for consulting and referencing the API.',
    summary='ReDoc UI'
)
class PublicSpectacularRedocView(SpectacularRedocView):
    permission_classes = [AllowAny]
    authentication_classes = []
