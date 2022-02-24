from django import forms
from .models import Organization, Membership
from account.models import User
from django.forms.widgets import Select


class OrganizationSettingsForm(forms.ModelForm):
    code = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}), disabled=True, required=False)
    members_can_edit = forms.BooleanField(widget=forms.CheckboxInput, help_text='Members will be able to edit contexts.', required=False)
    members_can_create = forms.BooleanField(widget=forms.CheckboxInput, help_text='Members will be able to create contexts.', required=False)

    class Meta:
        model = Organization
        fields = ['code', 'name', 'members_can_edit', 'members_can_create']


class OrganizationCreateForm(forms.ModelForm):

    class Meta:
        model = Organization
        fields = ['code', 'name']


class MembershipInviteForm(forms.Form):
    user = forms.EmailField(required=True)
