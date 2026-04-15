from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('company', 'Company'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    university = models.CharField(max_length=255)
    career = models.CharField(max_length=255)
    skills = models.TextField(blank=True)  
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)  # <-- línea nueva

    def __str__(self):
        if self.is_verified:
            return f"{self.user.username} - Estudiante Verificado"
        return f"{self.user.username} - Pendiente de verificación"
    cv_pdf = models.FileField(upload_to='cvs/', blank=True, null=True)  # US-10: upload CV


class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255)
    description = models.TextField()


class InternshipOffer(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('closed', 'Closed'),
    )

    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    desired_skills = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    MODALITY_CHOICES = (
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
        ('hibrido', 'Híbrido'),
    )
    modality = models.CharField(max_length=10, choices=MODALITY_CHOICES, default='presencial')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.company.company_name})"


class InternshipApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    offer = models.ForeignKey(InternshipOffer, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'offer')

    def save(self, *args, **kwargs):
        # once a decision is made, status may not be changed
        if self.pk:
            old = InternshipApplication.objects.get(pk=self.pk)
            if old.status != 'pending' and self.status != old.status:
                raise ValueError("Cannot modify application once decision has been made.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.user.username} - {self.offer.title} ({self.status})"
