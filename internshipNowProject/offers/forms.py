from django import forms
from offers.models import InternshipOffer



class CareersCharField(forms.CharField):
    def bound_data(self, data, initial):
        # If data is a list, join it as a string (for POST error cases)
        if isinstance(data, list):
            return ', '.join(str(x) for x in data)
        return data

class InternshipOfferForm(forms.ModelForm):
    careers = CareersCharField(required=True, widget=forms.HiddenInput, label='Required careers')

    class Meta:
        model = InternshipOffer
        fields = [
            'title',
            'description',
            'requirements',
            'desired_skills',
            'location',
            'salary',
            'modality',
            'status',
            'careers',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import Career
        # Only set initial from instance if this is not a POST (no form errors)
        if self.instance and self.instance.pk and not self.data:
            self.fields['careers'].initial = ', '.join(self.instance.careers.values_list('name', flat=True))

    def clean_careers(self):
        from accounts.models import Career
        careers_raw = self.cleaned_data.get('careers', '')
        # If careers_raw is a list, join it to a string
        if isinstance(careers_raw, list):
            careers_raw = ', '.join(str(x) for x in careers_raw)
        career_names = [c.strip() for c in careers_raw.split(',') if c.strip()]

        if not career_names:
            raise forms.ValidationError('Please select at least one career for this offer.')

        careers = []
        for name in career_names:
            try:
                career = Career.objects.get(name=name)
                careers.append(career)
            except Career.DoesNotExist:
                pass

        if not careers:
            raise forms.ValidationError('Please select valid careers for this offer.')

        return careers
