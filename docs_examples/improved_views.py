"""
Exemplos de como melhorar as views com documentação drf-spectacular avançada

Adicione essas melhorias às suas views existentes
"""

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter,
    inline_serializer,
)
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import serializers, status


# Exemplo de ViewSet com documentação completa
@extend_schema_view(
    list=extend_schema(
        summary="Listar barbearias",
        description="""
        ## Lista todas as barbearias cadastradas
        
        Este endpoint retorna uma lista paginada de barbearias com:
        - Filtros avançados por nome, localização e serviços
        - Busca por texto em nome e descrição
        - Ordenação por diferentes campos
        - Paginação automática (10 itens por página)
        
        ### Filtros Disponíveis:
        - `search`: Busca por nome ou descrição
        - `owner`: ID do proprietário
        - `ordering`: Ordenação (`name`, `-created_at`, etc.)
        
        ### Exemplos de Uso:
        - `GET /api/v1/barbershops/` - Lista todas
        - `GET /api/v1/barbershops/?search=central` - Busca por "central"
        - `GET /api/v1/barbershops/?ordering=-created_at` - Mais recentes primeiro
        """,
        tags=["barbershops"],
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Buscar por nome ou descrição da barbearia",
                examples=[
                    OpenApiExample("Busca por nome", value="Central"),
                    OpenApiExample("Busca por descrição", value="moderna"),
                ],
            ),
            OpenApiParameter(
                name="owner",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filtrar por ID do proprietário",
                examples=[
                    OpenApiExample("Proprietário específico", value=1),
                ],
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Campo para ordenação",
                enum=[
                    "name",
                    "-name",
                    "created_at",
                    "-created_at",
                    "updated_at",
                    "-updated_at",
                ],
                examples=[
                    OpenApiExample("Nome A-Z", value="name"),
                    OpenApiExample("Mais recentes", value="-created_at"),
                ],
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=BarbershopListSerializer,
                description="Lista de barbearias retornada com sucesso",
                examples=[
                    OpenApiExample(
                        "Lista de barbearias",
                        value={
                            "count": 25,
                            "next": "http://api.example.com/barbershops/?page=2",
                            "previous": None,
                            "results": [
                                {
                                    "id": 1,
                                    "name": "Barbearia Central",
                                    "description": "Barbearia moderna",
                                    "address": "Rua Principal, 123",
                                    "phone": "(11) 99999-9999",
                                    "total_services": 5,
                                    "average_service_price": "25.00",
                                }
                            ],
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Parâmetros inválidos",
                examples=[
                    OpenApiExample(
                        "Parâmetro inválido",
                        value={"error": "Parâmetro 'ordering' inválido"},
                    )
                ],
            ),
        },
    ),
    create=extend_schema(
        summary="Criar nova barbearia",
        description="""
        ## Cria uma nova barbearia no sistema
        
        Este endpoint permite que proprietários cadastrem suas barbearias.
        
        ### Validações:
        - CNPJ deve ser único e válido
        - Email deve ser único no sistema
        - Telefone deve estar no formato brasileiro
        - Usuário deve ter permissão de proprietário
        
        ### Campos Obrigatórios:
        - `name`: Nome da barbearia
        - `cnpj`: CNPJ válido
        - `address`: Endereço completo
        - `email`: Email de contato
        - `phone`: Telefone de contato
        """,
        tags=["barbershops"],
        request=BarbershopCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=BarbershopDetailSerializer,
                description="Barbearia criada com sucesso",
            ),
            400: OpenApiResponse(
                description="Dados inválidos",
                examples=[
                    OpenApiExample(
                        "CNPJ já existe",
                        value={"cnpj": ["Barbearia com este CNPJ já existe."]},
                    ),
                    OpenApiExample(
                        "Email inválido",
                        value={"email": ["Insira um endereço de email válido."]},
                    ),
                ],
            ),
            401: "Não autenticado",
            403: "Sem permissão para criar barbearias",
        },
    ),
    retrieve=extend_schema(
        summary="Obter detalhes da barbearia",
        description="""
        ## Retorna detalhes completos de uma barbearia específica
        
        Este endpoint retorna informações detalhadas incluindo:
        - Dados básicos da barbearia
        - Estatísticas (total de serviços, clientes, receita)
        - Informações de contato formatadas
        - Dados de auditoria (criação/atualização)
        """,
        tags=["barbershops"],
        responses={
            200: BarbershopDetailSerializer,
            404: OpenApiResponse(
                description="Barbearia não encontrada",
                examples=[
                    OpenApiExample(
                        "Não encontrada", value={"detail": "Não encontrado."}
                    )
                ],
            ),
        },
    ),
)
class ImprovedBarbershopViewSet(viewsets.ModelViewSet):
    # ... sua implementação atual ...

    @extend_schema(
        summary="Horários disponíveis para agendamento",
        description="""
        ## Consulta horários disponíveis em uma data específica
        
        Este endpoint retorna os horários livres para agendamento considerando:
        - Agenda do barbeiro na data solicitada
        - Agendamentos já existentes
        - Duração do serviço solicitado
        - Horário de funcionamento
        
        ### Como usar:
        1. Informe a data desejada no formato YYYY-MM-DD
        2. Opcionalmente informe a duração em minutos
        3. Receba lista de horários disponíveis
        """,
        tags=["appointments"],
        parameters=[
            OpenApiParameter(
                name="date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Data para consultar horários (YYYY-MM-DD)",
                examples=[
                    OpenApiExample("Data hoje", value="2024-01-15"),
                    OpenApiExample("Próxima semana", value="2024-01-22"),
                ],
            ),
            OpenApiParameter(
                name="duration",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Duração do serviço em minutos (padrão: 30)",
                examples=[
                    OpenApiExample("Corte simples", value=30),
                    OpenApiExample("Corte + barba", value=45),
                ],
            ),
        ],
        responses={
            200: inline_serializer(
                name="AvailableSlotsResponse",
                fields={
                    "date": serializers.DateField(help_text="Data consultada"),
                    "weekday": serializers.IntegerField(
                        help_text="Dia da semana (0=segunda, 6=domingo)"
                    ),
                    "available_slots": serializers.ListField(
                        child=serializers.TimeField(),
                        help_text="Lista de horários disponíveis no formato HH:MM",
                    ),
                    "total_slots": serializers.IntegerField(
                        help_text="Total de horários disponíveis"
                    ),
                },
            ),
            400: OpenApiResponse(
                description="Parâmetros inválidos",
                examples=[
                    OpenApiExample(
                        "Data obrigatória",
                        value={
                            "error": "Parâmetro 'date' é obrigatório (formato: YYYY-MM-DD)"
                        },
                    ),
                    OpenApiExample(
                        "Data inválida",
                        value={"error": "Formato de data inválido. Use YYYY-MM-DD"},
                    ),
                ],
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="available-slots")
    def available_slots(self, request, pk=None):
        # ... sua implementação atual ...
        pass
