from django.contrib import admin
from app.sms_api import models

# Register your models here.

# Inscription de tous les modèles dans le panel d'administration Django (Section 7 du tuto)
admin.site.register(models.Departments)
admin.site.register(models.Courses)
admin.site.register(models.Students)
admin.site.register(models.Teachers)
admin.site.register(models.Enrollments)
