from django import forms
from offers.models import InternshipOffer


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
