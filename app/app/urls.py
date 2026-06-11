"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='api-schema'),
        name='api-docs',
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )


# ==============================================================================
# AJOUTS POUR LES ROUTES DU PROJET STUDENT MANAGEMENT SYSTEM (SMS)
# ==============================================================================

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from django.urls import include

# 1. Injection dynamique du rôle dans le modèle User actif de la production
User = get_user_model()

@property
def get_user_role(self):
    if self.is_superuser:
        return 'ADMIN'
    elif self.groups.filter(name='TEACHER').exists():
        return 'TEACHER'
    elif self.groups.filter(name='STUDENT').exists():
        return 'STUDENT'
    return None

User.role = get_user_role

# 2. Ajout de tes routes d'API et de connexion à la suite de la liste existante
urlpatterns += [
    # Routes pour le JWT (Authentification)
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Inclusion des routes de ton application d'école
    path('api/', include('sms_api.urls')),
]


# ==============================================================================
# AJOUTS POUR WEBSOCKETS
# ==============================================================================

urlpatterns += [
    path("chat/", include("chat.urls")),
]
