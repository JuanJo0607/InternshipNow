from django import forms
from applications.models import InternshipApplication


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


class ApplicationFeedbackForm(forms.ModelForm):
    class Meta:
        model = InternshipApplication
        fields = ['feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'class': 'w-full rounded-xl border border-[#D1D5DB] px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#111827]',
                'rows': 4,
                'placeholder': 'Write feedback for this candidate...'
            })
        }
        labels = {
            'feedback': 'Feedback'
        }