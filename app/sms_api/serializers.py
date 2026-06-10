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
    """Sérialiseur conservant l'interface d'origine (username, first_name, last_name)"""

    # 🌟 On déclare explicitement tes champs d'origine en tant que champs virtuels
    username = serializers.CharField(write_only=True)  # Si non stocké, utilisable au POST
    first_name = serializers.CharField(source='get_first_name', required=False)
    last_name = serializers.CharField(source='get_last_name', required=False)

    role = serializers.SerializerMethodField()
    role_input = serializers.ChoiceField(
        choices=(('ADMIN', 'Admin'), ('TEACHER', 'Teacher'), ('STUDENT', 'Student')),
        write_only=True,
        source='role'
    )

    class Meta:
        model = User
        # Tes champs d'origine restent visibles à l'extérieur !
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'role', 'role_input')
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}
        }

    # --- Logique de lecture (GET) ---
    def get_first_name(self, obj):
        # On extrait le premier mot du champ 'name'
        return obj.name.split(' ')[0] if obj.name else ""

    def get_last_name(self, obj):
        # On extrait le reste du champ 'name'
        parts = obj.name.split(' ')
        return ' '.join(parts[1:]) if len(parts) > 1 else ""

    def get_role(self, obj):
        if obj.is_superuser:
            return 'ADMIN'
        from sms_api.models import Teachers, Students
        if Teachers.objects.filter(email=obj.email).exists():
            return 'TEACHER'
        if Students.objects.filter(email=obj.email).exists():
            return 'STUDENT'
        return 'UNKNOWN'

    # --- Logique d'écriture (POST) ---
    def create(self, validated_data):
        role = validated_data.pop('role', 'STUDENT')

        # 1. On intercepte tes champs d'origine
        username = validated_data.pop('username', None) # Utilisé si ton UserManager en a besoin
        first_name = validated_data.pop('get_first_name', '')
        last_name = validated_data.pop('get_last_name', '')

        # 2. On les fusionne pour remplir le champ unique 'name' attendu par ton modèle
        validated_data['name'] = f"{first_name} {last_name}".strip() or username

        # 3. Création de l'utilisateur
        user = User.objects.create_user(**validated_data)

        # 4. Attribution des rôles
        if role == 'ADMIN':
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False

        user.save()
        return user
