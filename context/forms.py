from django import forms
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from common.forms import DynamicArrayField
from .models import SearchContext, Configuration, Gatherer, AdvancedConfiguration, COUNTRY_CHOICES
import re


class SearchContextCreateForm(forms.ModelForm):
    code = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}), disabled=True, required=False)
    owner = forms.ChoiceField()

    error_messages = {
        'duplicate_code': 'A context you have access to already has that code.',
        'invalid_name': 'Invalid name.'
    }

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
            raise ValidationError(self.error_messages['invalid_name'], code='invalid_name')
        return cleaned_name

    def clean(self):
        code = self.cleaned_data.get('name', None)
        if code is None:
            raise ValidationError(self.error_messages['invalid_name'], code='invalid_name')

        code = code.replace(' ', '-').lower()
        if self.user.all_contexts.filter(code=code).exists():
            self.add_error('code', self.error_messages['duplicate_code'])

    class Meta:
        model = SearchContext
        fields = ['owner', 'code', 'name', 'description']


class EssentialConfigurationForm(forms.ModelForm):

    class Meta:
        model = Configuration
        fields = ['search_string', 'keywords', 'data_type']


class AdvancedConfigurationForm(forms.ModelForm):
    country_of_search = forms.ChoiceField(choices=COUNTRY_CHOICES)
    gatherers = forms.ModelMultipleChoiceField(queryset=Gatherer.objects.filter(is_active=True), required=False)
    seed_urls = DynamicArrayField(base_field=forms.URLField, required=False, help_text='The URLs you provide in this field will be crawled to find more results.', invalid_message='The element in the position %(nth)s has an invalid URL.')

    error_messages = {
        'incompatibility': 'The use of the gatherer %s is incompatible with the use of the gatherer %s.',
    }

    def clean_gatherers(self):
        # Check if there is an element of the gatherers that is in gatherer.incompatible_with. There probablly is a better way to do this
        gatherers: QuerySet[Gatherer] = self.cleaned_data["gatherers"]
        for gatherer in gatherers:
            incompatible_gatherers = gatherer.incompatible_with.filter(is_active=True)
            for incompatible_gatherer in incompatible_gatherers:
                if incompatible_gatherer in gatherers:
                    raise ValidationError(self.error_messages['incompatibility'], params=(gatherer, incompatible_gatherer), code='incompatibility')

        return gatherers

    class Meta:
        model = AdvancedConfiguration
        fields = ['country_of_search', 'seed_urls', 'gatherers']
