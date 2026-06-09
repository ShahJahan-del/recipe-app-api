from rest_framework import permissions
from sms_api import models

class IsAdminUser(permissions.BasePermission):
    """L'admin est soit un superuser Django, soit explicitement défini."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'is_staff', False))

class IsTeacherUser(permissions.BasePermission):
    """Vérifie si l'utilisateur connecté existe dans la table Teachers de Supabase."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return models.Teachers.objects.filter(email=request.user.email).exists()

class IsStudentUser(permissions.BasePermission):
    """Vérifie si l'utilisateur connecté existe dans la table Students de Supabase."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return models.Students.objects.filter(email=request.user.email).exists()
