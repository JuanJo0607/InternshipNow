from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, CompanyProfile

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
