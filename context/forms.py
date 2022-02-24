from django import forms
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet
from django.core.exceptions import ValidationError

from organization.models import Organization
from .models import SearchContext, Configuration
import re


class SearchContextCreateForm(forms.ModelForm):
    code = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}), disabled=True, required=False)
    owner = forms.ChoiceField()

    def __init__(self, user, *args, **kwargs):
        super(SearchContextCreateForm, self).__init__(*args, **kwargs)
        self.user = user
        # Choices are the current user, as well as the organizations where the user is active and he/she can create (if is owner he/she can always create)
        choices = [(self.user.email, f'(Me) {self.user.get_full_name()}')]
        organizations = self.user.organizations_active.filter(members_can_create=True) | self.user.organizations_active.filter(members_can_create=False, membership__is_owner=True)
        organizations = organizations.distinct()
        choices += [(org.code, f'(Organization) {org.name}') for org in organizations]
        self.fields['owner'].choices = choices

    def clean_name(self):
        # Strip and replace multiple spaces by a single space
        cleaned_name = re.sub(' +', ' ', self.cleaned_data['name'].strip())
        if cleaned_name == '':
            raise ValidationError('Invalid name.', code='invalid_name')
        return cleaned_name

    class Meta:
        model = SearchContext
        fields = ['owner', 'code', 'name', 'description']


class ConfigurationCreateForm(forms.ModelForm):

    class Meta:
        model = Configuration
        fields = ['search_string', 'keywords']
