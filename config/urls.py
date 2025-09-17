"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .schema import (
    PublicSpectacularAPIView,
    PublicSpectacularSwaggerView,
    PublicSpectacularRedocView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API v1 URLs - App Routes
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/barbershops/', include('apps.barbershops.urls')),
    path('api/v1/appointments/', include('apps.appointments.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),

    # JWT authentication URLs
    path('api/v1/auth/token/', include('apps.users.jwt_urls')),

    # API Documentation
    path('api/schema/', PublicSpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', PublicSpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', PublicSpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # DRF auth URLs
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)