from django import forms
from django.core.validators import EmailValidator

from .models import Proposal


class ProposalForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea,
        max_length=2000,
        strip=True,
    )
    submitter_name = forms.CharField(
        max_length=100,
        required=False,
        strip=True,
    )
    submitter_contact = forms.CharField(
        max_length=254,
        required=False,
        strip=True,
    )

    class Meta:
        model = Proposal
        fields = ['title', 'body', 'submitter_name', 'submitter_contact']

    def clean_submitter_contact(self):
        value = self.cleaned_data.get('submitter_contact', '').strip()
        if value:
            EmailValidator()(value)
        return value


class StatusChangeForm(forms.Form):
    new_status = forms.ChoiceField(choices=Proposal.STATUS_CHOICES)
