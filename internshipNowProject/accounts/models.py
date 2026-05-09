
from django.db import models
from django.contrib.auth.models import AbstractUser

class Career(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('company', 'Company'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cedula = models.CharField(max_length=20, blank=True)
    university = models.CharField(max_length=255, default='Universidad EAFIT')
    # career = models.CharField(max_length=255, blank=True)  # Deprecated, kept for migration
    careers = models.ManyToManyField('Career', blank=True, related_name='students')
    skills = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    cv_pdf = models.FileField(upload_to='cvs/', blank=True, null=True)

    def __str__(self):
        if self.is_verified:
            return f"{self.user.username} - Verified Student"
        return f"{self.user.username} - Pending verification"


class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255)
    description = models.TextField()
