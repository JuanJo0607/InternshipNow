from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User, StudentProfile, CompanyProfile


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label='First name')
    last_name = forms.CharField(max_length=150, required=True, label='Last name')
    cedula = forms.CharField(max_length=20, required=False, label='National ID')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'role', 'cedula', 'password1', 'password2')

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('role') == 'student' and not cleaned_data.get('cedula', '').strip():
            self.add_error('cedula', 'This field is required for students.')
        return cleaned_data


class StudentProfileForm(forms.ModelForm):

    first_name = forms.CharField(max_length=150, required=False, label='First name')
    last_name  = forms.CharField(max_length=150, required=False, label='Last name')
    cedula     = forms.CharField(max_length=20,  required=False, label='National ID')
    skills     = forms.CharField(required=False, widget=forms.Textarea)
    careers    = forms.CharField(required=False, widget=forms.HiddenInput, label='Careers')

    class Meta:
        model = StudentProfile
        fields = ['cedula', 'university', 'careers', 'skills', 'bio']

    field_order = ['first_name', 'last_name', 'cedula', 'university', 'careers', 'skills', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import Career
        self.fields['university'].initial = 'Universidad EAFIT'
        self.fields['university'].disabled = True
        self.fields['university'].widget.attrs['readonly'] = True
        if self.instance and self.instance.pk:
            self.fields['careers'].initial = ', '.join(self.instance.careers.values_list('name', flat=True))

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula', '').strip()
        if not cedula:
            raise forms.ValidationError('National ID cannot be left empty.')
        return cedula

    def clean_careers(self):
        from accounts.models import Career
        careers_raw = self.cleaned_data.get('careers', '')
        career_names = [c.strip() for c in careers_raw.split(',') if c.strip()]

        careers = []
        for name in career_names:
            try:
                career = Career.objects.get(name=name)
                careers.append(career)
            except Career.DoesNotExist:
                pass
        
        return careers


class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ['company_name', 'industry', 'description']


class StudentCVForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['cv_pdf']

    def clean_cv_pdf(self):
        file = self.cleaned_data.get('cv_pdf')
        if file:
            if not file.name.endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed.')
            if file.size > 5 * 1024 * 1024:  # 5 MB limit
                raise forms.ValidationError('File size must be under 5 MB.')
        return file
