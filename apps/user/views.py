from django.contrib.auth import update_session_auth_hash
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.user.models import User
from apps.user.permissions import (
    IsAdminOnly,
    IsAdminOrReadOnly,
    IsOwnerOrAdmin,
    IsOwnerOrAdminOrReadOnly,
)
from apps.user.serializers import (
    ChangePasswordSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from utils.throttles.custom_throttles import PasswordResetThrottle, AdminThrottle


# Create your views here.
@extend_schema_view(
    list=extend_schema(
        summary="Listar usuários",
        description="Lista todos os usuários com paginação e filtros.",
        tags=["users"],
    ),
    create=extend_schema(
        summary="Criar usuário",
        description="Cria um novo usuário no sistema.",
        tags=["users"],
    ),
    retrieve=extend_schema(
        summary="Detalhar usuário",
        description="Retorna os detalhes de um usuário específico.",
        tags=["users"],
    ),
    update=extend_schema(
        summary="Atualizar usuário",
        description="Atualiza todos os campos de um usuário.",
        tags=["users"],
    ),
    partial_update=extend_schema(
        summary="Atualizar usuário parcialmente",
        description="Atualiza alguns campos de um usuário.",
        tags=["users"],
    ),
    destroy=extend_schema(
        summary="Deletar usuário",
        description="Remove um usuário do sistema.",
        tags=["users"],
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar usuários com operações CRUD e ações customizadas.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [AdminThrottle]  # Throttling para operações administrativas
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["role", "is_barbershop_owner", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["date_joined", "updated_at", "username", "email"]
    ordering = ["-date_joined"]

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        elif self.action == "retrieve":
            return UserDetailSerializer
        elif self.action == "list":
            return UserListSerializer
        elif self.action == "change_password":
            return ChangePasswordSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Define as permissões baseadas na ação.
        """
        if self.action == "create":
            permission_classes = [AllowAny]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsOwnerOrAdminOrReadOnly]
        elif self.action in ["me", "change_password", "update_profile"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["deactivate", "activate"]:
            permission_classes = [IsAuthenticated, IsAdminOnly]
        elif self.action in ["stats", "admins"]:
            permission_classes = [IsAuthenticated, IsAdminOnly]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_throttles(self):
        """
        Retorna throttles apropriados baseado na ação.
        """
        if self.action == "change_password":
            throttle_classes = [PasswordResetThrottle]
        else:
            throttle_classes = self.throttle_classes

        return [throttle() for throttle in throttle_classes]

    @extend_schema(
        summary="Meu perfil",
        description="Retorna os dados do usuário autenticado.",
        tags=["users"],
    )
    @action(detail=False, methods=["get", "put", "patch"], url_path="me")
    def me(self, request):
        """
        Retorna ou atualiza os dados do usuário autenticado.
        """
        if request.method == "GET":
            serializer = UserDetailSerializer(
                request.user, context={"request": request}
            )
            return Response(serializer.data)
        elif request.method in ["PUT", "PATCH"]:
            serializer = UserUpdateSerializer(
                request.user,
                data=request.data,
                partial=request.method == "PATCH",
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    UserDetailSerializer(
                        request.user, context={"request": request}
                    ).data
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Alterar senha",
        description="Permite ao usuário alterar sua senha.",
        tags=["users"],
    )
    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        """
        Altera a senha do usuário autenticado.
        """
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            # Mantém o usuário logado após a mudança de senha
            update_session_auth_hash(request, user)

            return Response(
                {"message": "Senha alterada com sucesso."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Desativar usuário",
        description="Desativa um usuário específico (apenas administradores).",
        tags=["users"],
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsAdminOnly],
    )
    def deactivate(self, request, pk=None):
        """
        Desativa um usuário específico.
        """
        user = self.get_object()

        # Usando o novo método do modelo para verificar se pode ser desativado
        if not user.can_be_deactivated_by(request.user):
            return Response(
                {"error": "Você não tem permissão para desativar este usuário."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.is_active = False
        user.save()
        return Response(
            {"message": f"Usuário {user.get_display_name()} desativado com sucesso."}
        )

    @extend_schema(
        summary="Ativar usuário",
        description="Ativa um usuário específico (apenas administradores).",
        tags=["users"],
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsAdminOnly],
    )
    def activate(self, request, pk=None):
        """
        Ativa um usuário específico.
        """
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response(
            {"message": f"Usuário {user.get_display_name()} ativado com sucesso."}
        )

    @extend_schema(
        summary="Listar barbeiros",
        description="Lista todos os usuários com função de barbeiro.",
        tags=["users"],
    )
    @action(detail=False, methods=["get"], url_path="barbers")
    def barbers(self, request):
        """
        Lista todos os barbeiros usando o método otimizado do modelo.
        """
        barbers = User.get_barbers_queryset()

        # Aplicar filtros de busca se fornecidos
        search = request.query_params.get("search", None)
        if search:
            barbers = barbers.filter(
                models.Q(username__icontains=search)
                | models.Q(email__icontains=search)
                | models.Q(first_name__icontains=search)
                | models.Q(last_name__icontains=search)
            )

        page = self.paginate_queryset(barbers)
        if page is not None:
            serializer = UserListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserListSerializer(
            barbers, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Listar clientes",
        description="Lista todos os usuários com função de cliente.",
        tags=["users"],
    )
    @action(detail=False, methods=["get"], url_path="clients")
    def clients(self, request):
        """
        Lista todos os clientes usando o método otimizado do modelo.
        """
        clients = User.get_clients_queryset()

        # Aplicar filtros de busca se fornecidos
        search = request.query_params.get("search", None)
        if search:
            clients = clients.filter(
                models.Q(username__icontains=search)
                | models.Q(email__icontains=search)
                | models.Q(first_name__icontains=search)
                | models.Q(last_name__icontains=search)
            )

        page = self.paginate_queryset(clients)
        if page is not None:
            serializer = UserListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserListSerializer(
            clients, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Estatísticas de usuários",
        description="Retorna estatísticas gerais sobre usuários (apenas administradores).",
        tags=["users"],
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated, IsAdminOnly],
    )
    def stats(self, request):
        """
        Retorna estatísticas dos usuários usando o método otimizado do modelo.
        """
        stats = User.get_users_stats()
        return Response(stats)

    @extend_schema(
        summary="Listar administradores",
        description="Lista todos os usuários com função de administrador.",
        tags=["users"],
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="admins",
        permission_classes=[IsAuthenticated, IsAdminOnly],
    )
    def admins(self, request):
        """
        Lista todos os administradores usando o método otimizado do modelo.
        """
        admins = User.get_admins_queryset()

        # Aplicar filtros de busca se fornecidos
        search = request.query_params.get("search", None)
        if search:
            admins = admins.filter(
                models.Q(username__icontains=search)
                | models.Q(email__icontains=search)
                | models.Q(first_name__icontains=search)
                | models.Q(last_name__icontains=search)
            )

        page = self.paginate_queryset(admins)
        if page is not None:
            serializer = UserListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserListSerializer(admins, many=True, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Verificar tipo de usuário",
        description="Verifica o tipo do usuário atual (cliente, barbeiro ou admin).",
        tags=["users"],
    )
    @action(detail=False, methods=["get"], url_path="user-type")
    def user_type(self, request):
        """
        Retorna informações sobre o tipo de usuário atual.
        """
        user = request.user
        return Response(
            {
                "is_barber": user.is_barber(),
                "is_client": user.is_client(),
                "is_admin_user": user.is_admin_user(),
                "is_barbershop_owner": user.is_barbershop_owner,
                "role": user.role,
                "role_display": user.get_role_display_translated(),
            }
        )

    @extend_schema(
        summary="Completude do perfil",
        description="Retorna a porcentagem de completude do perfil do usuário atual.",
        tags=["users"],
    )
    @action(detail=False, methods=["get"], url_path="profile-completion")
    def profile_completion(self, request):
        """
        Retorna a porcentagem de completude do perfil do usuário atual.
        """
        user = request.user
        return Response(
            {
                "completion_percentage": user.get_profile_completion_percentage(),
                "has_profile_picture": user.has_profile_picture(),
            }
        )
