"""
URL configuration for sms_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.models import User
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

@property
def get_user_role(self):
    if self.is_superuser:
        return 'ADMIN'
    elif self.groups.filter(name='TEACHER').exists():
        return 'TEACHER'
    elif self.groups.filter(name='STUDENT').exists():
        return 'STUDENT'
    return None

# On injecte dynamiquement la propriété 'role' dans l'objet User de Django
User.role = get_user_role

urlpatterns = [
    path('admin/', admin.site.urls),
    # Routes pour le JWT :
    # La route 'login/' renverra un Access Token et un Refresh Token en échange d'un username/password
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('sms_api.urls')),
    # Routes pour la documentation Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
