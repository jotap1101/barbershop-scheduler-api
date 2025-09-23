"""
Exemplos de como melhorar os serializers com documentação drf-spectacular

Adicione isso aos seus serializers existentes para documentação mais rica
"""

from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from drf_spectacular.openapi import OpenApiExample
from rest_framework import serializers


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Barbershop Creation Example",
            summary="Exemplo de criação de barbearia",
            description="Exemplo completo de dados para criar uma nova barbearia",
            value={
                "name": "Barbearia Central",
                "description": "Barbearia moderna no centro da cidade",
                "cnpj": "12.345.678/0001-90",
                "address": "Rua Principal, 123 - Centro - São Paulo/SP",
                "email": "contato@barbeariacentral.com",
                "phone": "(11) 99999-9999",
                "logo": "https://example.com/logo.jpg",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Barbershop Response Example",
            summary="Exemplo de resposta de barbearia",
            description="Dados completos retornados ao consultar uma barbearia",
            value={
                "id": 1,
                "name": "Barbearia Central",
                "description": "Barbearia moderna no centro da cidade",
                "cnpj": "12.345.678/0001-90",
                "formatted_cnpj": "12.345.678/0001-90",
                "address": "Rua Principal, 123 - Centro - São Paulo/SP",
                "email": "contato@barbeariacentral.com",
                "phone": "(11) 99999-9999",
                "formatted_phone": "(11) 99999-9999",
                "logo": "https://example.com/logo.jpg",
                "total_services": 5,
                "available_services_count": 5,
                "average_service_price": "25.00",
                "total_customers": 150,
                "total_appointments": 1250,
                "total_revenue": "31250.00",
                "has_logo": True,
                "has_contact_info": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            },
            response_only=True,
        ),
    ]
)
class BarbershopCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de barbearias

    Este serializer é usado para criar novas barbearias no sistema.
    Todos os campos obrigatórios devem ser preenchidos.
    """

    @extend_schema_field(
        field={
            "type": "string",
            "format": "email",
            "description": "Email de contato da barbearia (deve ser único no sistema)",
            "example": "contato@barbeariacentral.com",
        }
    )
    def email(self):
        return serializers.EmailField()

    @extend_schema_field(
        field={
            "type": "string",
            "pattern": r"^\(\d{2}\)\s\d{4,5}-\d{4}$",
            "description": "Telefone no formato (XX) XXXXX-XXXX",
            "example": "(11) 99999-9999",
        }
    )
    def phone(self):
        return serializers.CharField()

    class Meta:
        model = Barbershop
        fields = ["name", "description", "cnpj", "address", "email", "phone", "logo"]
        extra_kwargs = {
            "name": {
                "help_text": "Nome da barbearia (máximo 255 caracteres)",
                "max_length": 255,
                "min_length": 2,
            },
            "description": {
                "help_text": "Descrição detalhada da barbearia e seus serviços",
                "required": False,
            },
            "cnpj": {
                "help_text": "CNPJ da barbearia no formato XX.XXX.XXX/XXXX-XX",
                "max_length": 18,
            },
        }
