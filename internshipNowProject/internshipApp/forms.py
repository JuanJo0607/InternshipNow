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


# US-10: Form para subir CV en PDF
class StudentCVForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['cv_pdf']

    def clean_cv_pdf(self):
        file = self.cleaned_data.get('cv_pdf')
        if file:
            if not file.name.endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed.')
            if file.size > 5 * 1024 * 1024:  # 5 MB límite
                raise forms.ValidationError('File size must be under 5 MB.')
        return file