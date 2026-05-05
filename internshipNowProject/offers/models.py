from django.db import models
from accounts.models import CompanyProfile, StudentProfile


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
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.company.company_name})"


class InternshipOfferView(models.Model):
    offer = models.ForeignKey(InternshipOffer, on_delete=models.CASCADE, related_name='views')
    student = models.ForeignKey(StudentProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='offer_views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        viewer = self.student.user.username if self.student else 'Anonymous'
        return f"View of {self.offer.title} by {viewer} on {self.viewed_at:%Y-%m-%d %H:%M}"
