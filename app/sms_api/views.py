from django.shortcuts import render
from app.sms_api import models, permissions
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from app.sms_api import serializers
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.db.models import Max
from rest_framework.exceptions import PermissionDenied # Import pour bloquer la modif d'email du prof

User = get_user_model()

# Create your views here.

class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.DepartmentSerializer
    queryset = models.Departments.objects.all()
    # Seul l'admin peut toucher aux départements
    permission_classes = [permissions.IsAdminUser]


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CourseSerializer

    def get_permissions(self):
        # L'admin peut tout faire (CRUD), le prof peut juste voir (Read-Only)
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()] # Il faut juste être connecté
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        user = self.request.user
        # L'admin voit tout (Nouveau commentaire : Sécurité Superuser)
        if user.is_superuser:
            return models.Courses.objects.all()

        # Si c'est un prof, il ne voit QUE ses cours assignés (Adapté avec liaison Email)
        teacher_profile = models.Teachers.objects.filter(email=user.email).first()
        if teacher_profile:
            return models.Courses.objects.filter(teacher=teacher_profile)

        # Si c'est un étudiant, il n'a pas accès à la liste globale des cours selon le CDC
        if models.Students.objects.filter(email=user.email).exists():
            return models.Courses.objects.none()

        # L'admin voit tout
        return models.Courses.objects.all()

    def perform_update(self, serializer):
        # 1. On récupère l'état du cours AVANT la modification
        old_course = self.get_object()
        old_teacher = old_course.teacher

        # 2. On sauvegarde les modifications de l'Admin
        course = serializer.save()
        new_teacher = course.teacher

        # 3. Si le professeur a changé (Assignation), on envoie l'e-mail
        if new_teacher and (old_teacher != new_teacher) and new_teacher.email:
            subject = f"Assignation de cours : {course.title}"
            message = (
                f"Bonjour Pr. {new_teacher.last_name},\n\n"
                f"L'administration vous a assigné le cours suivant : '{course.title}'.\n\n"
                f"Cordialement,\nL'administration."
            )
            send_mail(subject, message, 'noreply@ecole.fr', [new_teacher.email], fail_silently=False)


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.StudentSerializer

    def get_permissions(self):
        # L'admin peut gérer les profils, les profs et étudiants peuvent juste voir
        if self.action in ['retrieve', 'update', 'partial_update', 'list']:
            return [IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        user = self.request.user
        # L'admin voit tout (Nouveau commentaire : Sécurité Superuser)
        if user.is_superuser:
            return models.Students.objects.all()

        # Un étudiant ne peut voir QUE son propre profil (Adapté avec liaison Email)
        student_profile = models.Students.objects.filter(email=user.email).first()
        if student_profile:
            return models.Students.objects.filter(student_id=student_profile.student_id)

        # Un prof ne peut voir que les étudiants inscrits dans SES cours (Adapté avec liaison Email)
        teacher_profile = models.Teachers.objects.filter(email=user.email).first()
        if teacher_profile:
            # SÉCURITÉ : Si le prof tente de modifier (update), on lui bloque l'accès !
            if self.action in ['update', 'partial_update']:
                raise PermissionDenied("Un professeur ne peut pas modifier la fiche administrative d'un étudiant.")
            return models.Students.objects.filter(enrollments__course__teacher=teacher_profile).distinct()

        # L'admin voit tout
        return models.Students.objects.all()

    # SÉCURITÉ  : Limiter les modifications de l'étudiant (Nom uniquement)
    def perform_update(self, serializer):
        user = self.request.user

        # On vérifie si l'utilisateur qui fait le PUT/PATCH est un étudiant
        is_student = models.Students.objects.filter(email=user.email).exists()

        if is_student:
            # On récupère l'état actuel de sa fiche avant modification
            current_profile = self.get_object()

            # SÉCURITÉ CDC : On supprime ou écrase toutes les données interdites
            # Si l'étudiant a tenté de modifier ces champs, on remet de force les valeurs de la base de données
            serializer.validated_data['student_id'] = current_profile.student_id  # Bloqué
            serializer.validated_data['email'] = current_profile.email
            serializer.validated_data['age_category'] = current_profile.age_category
            serializer.validated_data['sex'] = current_profile.sex
            serializer.validated_data['wsh'] = current_profile.wsh
            serializer.validated_data['dca'] = current_profile.dca

            # Optionnel : Modification du mot de passe dans l'authentification Django si transmise
            raw_password = self.request.data.get('password')
            if raw_password:
                user.set_password(raw_password)
                user.save()

        # Sauvegarde finale sécurisée (Seuls first_name et last_name seront réellement mis à jour)
        serializer.save()



class TeacherViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TeacherSerializer

    # Seul l'admin peut modifier la liste globale des profs,
    # mais les utilisateurs connectés peuvent la consulter
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update']:
            return [IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        user = self.request.user
        # L'admin voit tout (Nouveau commentaire : Sécurité Superuser)
        if user.is_superuser:
            return models.Teachers.objects.all()

        # Ajout N°4 : Un prof ne voit et ne modifie que ses propres données (Email non modifiable)
        teacher_profile = models.Teachers.objects.filter(email=user.email).first()
        if teacher_profile:
            if self.action in ['update', 'partial_update'] and self.request.data.get('email'):
                if self.request.data.get('email') != teacher_profile.email:
                    raise PermissionDenied("Modification de l'adresse email interdite.")
            return models.Teachers.objects.filter(teacher_id=teacher_profile.teacher_id)

        # Tout le monde voit la liste des profs
        return models.Teachers.objects.all()


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.EnrollmentSerializer

    def get_permissions(self):
        # L'admin et le Teacher peuvent gérer les inscriptions (Adapté avec IsAuthenticated pour DRF standard)
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        # L'admin voit toutes les inscriptions (Nouveau commentaire)
        if user.is_superuser or models.Teachers.objects.filter(email=user.email).first() is None and models.Students.objects.filter(email=user.email).first() is None:
            return models.Enrollments.objects.all()

        # Le prof ne voit que les inscriptions aux cours qu'il donne (Adapté avec liaison Email)
        teacher_profile = models.Teachers.objects.filter(email=user.email).first()
        if teacher_profile:
            return models.Enrollments.objects.filter(course__teacher=teacher_profile)

        # L'étudiant ne voit que ses propres inscriptions (Adapté avec liaison Email)
        student_profile = models.Students.objects.filter(email=user.email).first()
        if student_profile:
            return models.Enrollments.objects.filter(student=student_profile)

        return models.Enrollments.objects.none()

    # INTERCEPTION DE LA CRÉATION POUR L'ENVOI D'EMAIL
    def perform_create(self, serializer):
        user = self.request.user
        student_profile = models.Students.objects.filter(email=user.email).first()

        # Sécurité Ajout N°4 : Si c'est un étudiant qui crée, il est forcé de s'inscrire lui-même
        if student_profile:
            enrollment = serializer.save(student=student_profile)
        else:
            # L'admin ou le prof choisissent librement l'étudiant dans le formulaire
            enrollment = serializer.save()

        # 2. On récupère dynamiquement les objets liés pour personnaliser le message
        student = enrollment.student
        course = enrollment.course
        teacher = course.teacher # Ajout pour récupérer le prof du cours

        # 3. Rédaction de l'e-mail (Notification pour l'Étudiant)
        subject = f"Confirmation d'inscription : {course.title}"
        message = (
            f"Bonjour {student.first_name} {student.last_name},\n\n"
            f"Nous te confirmons ton inscription au cours '{course.title}' "
            f"dispensé par le professeur {course.teacher.first_name} {course.teacher.last_name}.\n\n"
            f"Cordialement,\nL'administration de l'école."
        )
        recipient_list = [student.email]

        # 4. Envoi via le système natif de Django
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@ecole.fr',
            recipient_list=recipient_list,
            fail_silently=False, # Permet de lever une erreur dans le terminal si l'envoi échoue
        )

        # AJOUT N°5 : Notification manquante pour le Professeur de la classe
        if teacher and teacher.email:
            subject_teacher = f"Nouvel étudiant inscrit : {course.title}"
            message_teacher = (
                f"Bonjour Pr. {teacher.last_name},\n\n"
                f"L'étudiant {student.first_name} {student.last_name} s'est inscrit à votre cours '{course.title}'.\n\n"
                f"Cordialement,\nL'administration."
            )
            send_mail(subject_teacher, message_teacher, 'noreply@ecole.fr', [teacher.email], fail_silently=False)

    # AJOUT N°5 : Interception de la suppression pour les alertes de désinscription du CDC
    def perform_destroy(self, instance):
        student = instance.student
        course = instance.course
        teacher = course.teacher

        # Suppression de l'inscription
        instance.delete()

        # Mail à l'étudiant retiré
        send_mail(f"Désinscription : {course.title}", f"Bonjour {student.first_name}, vous avez été retiré du cours {course.title}.", 'noreply@ecole.fr', [student.email], fail_silently=True)

        # Mail au professeur concerné
        if teacher and teacher.email:
            send_mail(f"Départ d'un étudiant : {course.title}", f"L'étudiant {student.first_name} {student.last_name} a quitté le cours {course.title}.", 'noreply@ecole.fr', [teacher.email], fail_silently=True)


class AdminUserManagementViewSet(viewsets.ModelViewSet):
    """Gestion des comptes par l'Admin + Envoi d'email (Section 10.2)"""
    serializer_class = serializers.AdminUserCreationSerializer
    queryset = User.objects.all()

    # Seul l'utilisateur ayant le rôle 'ADMIN' a le droit d'accéder à ce ViewSet
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        # 1. Récupération des données saisies dans le formulaire d'administration
        raw_password = self.request.data.get('password')
        role = self.request.data.get('role')
        email_saisi = self.request.data.get('email')

        # SÉCURITÉ DE CORRESPONDANCE DES DONNÉES AVEC SUPABASE
        # Avant de sauvegarder l'utilisateur Django, on vérifie s'il existe déjà dans Supabase
        if role == 'TEACHER':
            existing_profile = models.Teachers.objects.filter(email=email_saisi).first()
            if existing_profile:
                # On force l'alignement des données : Django prend les valeurs exactes de Supabase
                serializer.validated_data['id'] = existing_profile.teacher_id
                serializer.validated_data['first_name'] = existing_profile.first_name
                serializer.validated_data['last_name'] = existing_profile.last_name

        elif role == 'STUDENT':
            existing_profile = models.Students.objects.filter(email=email_saisi).first()
            if existing_profile:
                # On force l'alignement des données : Django prend les valeurs exactes de Supabase
                serializer.validated_data['id'] = existing_profile.student_id
                serializer.validated_data['first_name'] = existing_profile.first_name
                serializer.validated_data['last_name'] = existing_profile.last_name

        # 2. Sauvegarde de l'utilisateur Django (Désormais 100% raccord avec Supabase)
        user = serializer.save()

        # 3. CRÉATION AUTOMATIQUE SI LE PROFIL N'EXISTE PAS ENCORE
        if role == 'TEACHER':
            if not models.Teachers.objects.filter(email=user.email).exists():
                max_id = models.Teachers.objects.aggregate(Max('teacher_id'))['teacher_id__max']
                next_id = (max_id or 0) + 1
                models.Teachers.objects.create(
                    teacher_id=next_id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email
                )

        elif role == 'STUDENT':
            if not models.Students.objects.filter(email=user.email).exists():
                max_id = models.Students.objects.aggregate(Max('student_id'))['student_id__max']
                next_id = (max_id or 0) + 1
                models.Students.objects.create(
                    student_id=next_id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,
                    age_category="Adult",
                    sex="Not Specified",
                    wsh="N/A",
                    dca="N/A"
                )

        # 4. Envoi de l'e-mail avec les accès (Utilise les vraies données synchronisées)
        subject = f"Vos identifiants de connexion - École ({role})"
        message = (
            f"Bonjour {user.first_name} {user.last_name},\n\n"
            f"L'administrateur vous a créé un compte avec le rôle : {role}.\n\n"
            f"Voici vos accès pour vous connecter :\n"
            f" - Identifiant (Username) : {user.username}\n"
            f" - Mot de passe : {raw_password}\n\n"
            f"Cordialement,\n L'administration."
        )
        send_mail(subject, message, 'noreply@ecole.fr', [user.email], fail_silently=False)
