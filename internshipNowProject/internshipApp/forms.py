from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, CompanyProfile, InternshipOffer

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['university', 'career', 'skills', 'bio']


class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ['company_name', 'industry', 'description']


class InternshipOfferForm(forms.ModelForm):
    class Meta:
        model = InternshipOffer
        # exclude company and created_at; company will be set in view
        fields = [
            'title',
            'description',
            'requirements',
            'desired_skills',
            'location',
            'salary',
            'modality',
            'status',
        ]
