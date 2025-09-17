from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from .utils import IsOwnerOrAdmin
from django.core.cache import cache
from rest_framework.permissions import AllowAny, IsAdminUser

User = get_user_model()

@extend_schema_view(
    list=extend_schema(
        description='List all users. Only accessible by admins.',
        tags=['Users']
    ),
    create=extend_schema(
        description='Create a new user. Publicly accessible.',
        tags=['Users']
    ),
    retrieve=extend_schema(
        description='Get details of a specific user.',
        tags=['Users']
    ),
    update=extend_schema(
        description='Update a user. Only accessible by the owner or admin.',
        tags=['Users']
    ),
    partial_update=extend_schema(
        description='Partially update a user. Only accessible by the owner or admin.',
        tags=['Users']
    ),
    destroy=extend_schema(
        description='Delete a user. Only accessible by the owner or admin.',
        tags=['Users']
    ),
    bulk_delete=extend_schema(
        description='Bulk delete users. Only accessible by admins.',
        tags=['Users']
    ),
    change_password=extend_schema(
        description='Change password for a user. Accessible by the user themselves or admins.',
        tags=['Users']
    )
)
class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrAdmin]
    filterset_fields = ['role']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username']

    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ['list', 'bulk_delete']:
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Deletar os usuários
        User.objects.filter(id__in=ids).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'detail': 'Both old_password and new_password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(old_password):
            return Response(
                {'detail': 'Old password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed successfully'})

    def get_queryset(self):
        # Return 403 before 404 for unauthorized access
        if self.action not in ['create', 'list', 'bulk_delete']:
            try:
                user_id = int(self.kwargs.get('pk'))
                if not self.request.user.is_authenticated:
                    raise PermissionDenied("Authentication required")
                if not self.request.user.is_staff and user_id != self.request.user.id:
                    raise PermissionDenied("You don't have permission to modify other users")
            except (TypeError, ValueError):
                pass

        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(id=self.request.user.id)
        return queryset

    def perform_create(self, serializer):
        user = serializer.save()

    def perform_update(self, serializer):
        user = serializer.save()

    def perform_destroy(self, instance):
        instance.delete()
