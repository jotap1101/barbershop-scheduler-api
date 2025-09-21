from django.contrib.auth import update_session_auth_hash
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.user.models import User
from apps.user.permissions import (
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
            permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

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
        permission_classes=[IsAuthenticated, IsAdminOrReadOnly],
    )
    def deactivate(self, request, pk=None):
        """
        Desativa um usuário específico.
        """
        user = self.get_object()
        if user.role == User.Role.ADMIN and request.user != user:
            return Response(
                {"error": "Não é possível desativar outro administrador."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.is_active = False
        user.save()
        return Response({"message": f"Usuário {user.username} desativado com sucesso."})

    @extend_schema(
        summary="Ativar usuário",
        description="Ativa um usuário específico (apenas administradores).",
        tags=["users"],
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsAdminOrReadOnly],
    )
    def activate(self, request, pk=None):
        """
        Ativa um usuário específico.
        """
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({"message": f"Usuário {user.username} ativado com sucesso."})

    @extend_schema(
        summary="Listar barbeiros",
        description="Lista todos os usuários com função de barbeiro.",
        tags=["users"],
    )
    @action(detail=False, methods=["get"], url_path="barbers")
    def barbers(self, request):
        """
        Lista todos os barbeiros.
        """
        barbers = User.objects.filter(role=User.Role.BARBER, is_active=True)

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
        Lista todos os clientes.
        """
        clients = User.objects.filter(role=User.Role.CLIENT, is_active=True)

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
        permission_classes=[IsAuthenticated, IsAdminOrReadOnly],
    )
    def stats(self, request):
        """
        Retorna estatísticas dos usuários.
        """
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users

        by_role = {}
        for role_choice in User.Role.choices:
            role_key = role_choice[0]
            role_label = role_choice[1]
            count = User.objects.filter(role=role_key).count()
            by_role[role_key] = {"label": role_label, "count": count}

        barbershop_owners = User.objects.filter(is_barbershop_owner=True).count()

        return Response(
            {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "users_by_role": by_role,
                "barbershop_owners": barbershop_owners,
            }
        )
