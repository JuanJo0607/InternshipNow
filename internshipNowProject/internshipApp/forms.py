from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, CompanyProfile, InternshipOffer, InternshipApplication

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')



class StudentProfileForm(forms.ModelForm):
    skills = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = StudentProfile
        fields = ['university', 'career', 'skills', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['university'].initial = 'Universidad EAFIT'
        self.fields['university'].disabled = True
        self.fields['university'].widget.attrs['readonly'] = True


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


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = InternshipApplication
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # only allow moving from pending to accepted/rejected
        if self.instance and self.instance.pk:
            if self.instance.status == 'pending':
                self.fields['status'].choices = [
                    ('accepted', 'Accepted'),
                    ('rejected', 'Rejected'),
                ]
            else:
                # disable field if already decided
                self.fields['status'].disabled = True

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

