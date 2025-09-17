from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import IsAuthenticated

@extend_schema(
    description='Obtain JWT token pair and user info.',
    tags=['Authentication']
)
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Add user info to response
        if response.status_code == status.HTTP_200_OK:
            # Get the user from the serializer
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            response.data.update({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            })
        
        return response

@extend_schema(
    description='Refresh access token using refresh token.',
    tags=['Authentication']
)
class CustomTokenRefreshView(TokenRefreshView):
    pass

@extend_schema(
    description='Verify if a token is valid.',
    tags=['Authentication']
)
class CustomTokenVerifyView(TokenVerifyView):
    pass

class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)

    def validate_refresh_token(self, value):
        try:
            RefreshToken(value)
            return value
        except TokenError:
            raise serializers.ValidationError("Invalid refresh token.")

@extend_schema(
    description='Logout user by blacklisting their refresh token.',
    tags=['Authentication']
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            token = RefreshToken(serializer.validated_data['refresh_token'])
            token.blacklist()
            return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)