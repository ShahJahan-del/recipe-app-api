from rest_framework import serializers
from sms_api import models
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
User = get_user_model()

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Departments
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Courses
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Students
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Teachers
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Enrollments
        fields = '__all__'


# Old Admin Serializer (when User was created in the same project app, no problem accessing roles)
#class AdminUserCreationSerializer(serializers.ModelSerializer):
#    """Création de compte par l'Admin (Inspiré Section 10)"""
#    role = serializers.ChoiceField(choices=(('ADMIN', 'Admin'), ('TEACHER', 'Teacher'), ('STUDENT', 'Student')), write_only=True)

#    class Meta:
#        model = User
#        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'role')
#        extra_kwargs = {
#            'password': {
#                'write_only': True,
#                'style': {'input_type': 'password'}
#            }
#        }

#    def create(self, validated_data):
#        # 1. On extrait le rôle pour la logique de la vue
#        role = validated_data.pop('role')

#        # 2. On crée l'utilisateur Django standard
#        user = User.objects.create_user(**validated_data)

#        # 3. Droits d'accès au back-office si ADMIN
#        if role == 'ADMIN':
#            user.is_staff = True
#            user.is_superuser = True
#        else:
#            user.is_staff = False
#            user.is_superuser = False

#        user.save()
#        return user


# New Admin Serializer (User is created in core, which has no roles, problem accessing them automatically)
class AdminUserCreationSerializer(serializers.ModelSerializer):
    """Création de compte par l'Admin (Inspiré Section 10)"""
    # On retire le write_only=True pur et on utilise un SerializerMethodField pour la lecture
    role = serializers.SerializerMethodField()
    # On ajoute un champ dédié à la saisie lors du POST pour ne pas perturber la validation
    role_input = serializers.ChoiceField(
        choices=(('ADMIN', 'Admin'), ('TEACHER', 'Teacher'), ('STUDENT', 'Student')),
        write_only=True,
        source='role' # Fait croire à DRF que ce champ remplit 'role'
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'role', 'role_input')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'style': {'input_type': 'password'}
            }
        }

    def get_role(self, obj):
        """ Permet au GET et à la DOC de lire le rôle sans faire planter Django"""
        if obj.is_superuser:
            return 'ADMIN'
        # On regarde dynamiquement si l'utilisateur a une fiche étudiant ou prof
        from sms_api.models import Teachers, Students
        if Teachers.objects.filter(email=obj.email).exists():
            return 'TEACHER'
        if Students.objects.filter(email=obj.email).exists():
            return 'STUDENT'
        return 'UNKNOWN'

    def create(self, validated_data):
        # 1. On extrait le rôle (qui arrive via source='role')
        role = validated_data.pop('role', 'STUDENT')

        # 2. On crée l'utilisateur Django standard
        user = User.objects.create_user(**validated_data)

        # 3. Droits d'accès au back-office si ADMIN
        if role == 'ADMIN':
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False

        user.save()
        return user
