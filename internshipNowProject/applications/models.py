from django.db import models
from accounts.models import StudentProfile
from offers.models import InternshipOffer


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
