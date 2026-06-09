# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

ROLE_CHOICES = (
    ('ADMIN', 'Admin'),
    ('TEACHER', 'Teacher'),
    ('STUDENT', 'Student'),
)

class Courses(models.Model):
    course_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=100)
    credits = models.IntegerField(blank=True, null=True)
    department = models.ForeignKey('Departments', models.DO_NOTHING, blank=True, null=True)
    teacher = models.ForeignKey('Teachers', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'courses'


class Departments(models.Model):
    department_id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = True
        db_table = 'departments'


class Enrollments(models.Model):
    enrollment_id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Students', models.DO_NOTHING)
    course = models.ForeignKey(Courses, models.DO_NOTHING)
    enrollment_date = models.DateField(blank=True, null=True)
    grade = models.CharField(max_length=5)

    class Meta:
        managed = True
        db_table = 'enrollments'


class Students(models.Model):
    student_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(unique=True, max_length=100)
    age_category = models.CharField(max_length=20)
    sex = models.CharField(max_length=50)
    wsh = models.CharField(max_length=50)
    dca = models.CharField(max_length=5)

    class Meta:
        managed = True
        db_table = 'students'


class Teachers(models.Model):
    teacher_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(unique=True, max_length=100)
    department = models.ForeignKey(Departments, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'teachers'
