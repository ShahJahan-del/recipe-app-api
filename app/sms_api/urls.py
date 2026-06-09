from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.sms_api import views
from rest_framework.authtoken import views as token_views

router = DefaultRouter()
router.register('departments', views.DepartmentViewSet)
router.register('courses', views.CourseViewSet, basename='courses')
router.register('students', views.StudentViewSet, basename='students')
router.register('teachers', views.TeacherViewSet, basename='teachers')
router.register('enrollments', views.EnrollmentViewSet, basename='enrollments')
router.register('users-admin', views.AdminUserManagementViewSet, basename='users-admin')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', token_views.obtain_auth_token, name='login'),
]
