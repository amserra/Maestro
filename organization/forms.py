from django import forms
from .models import Organization


class OrganizationCreateForm(forms.ModelForm):

    class Meta:
        model = Organization
        fields = ['code', 'name']
