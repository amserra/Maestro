import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from easy_select2 import Select2Multiple
from common.forms import DynamicArrayField
from .models import SearchContext, Configuration, Fetcher, Filter, AdvancedConfiguration, COUNTRY_CHOICES, PostProcessor, Classifier
import re
from django.utils import timezone


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


class TextInputWithMap(forms.TextInput):
    template_name = 'common/input_map.html'


class FetchingAndGatheringConfigurationForm(forms.ModelForm):
    country_of_search = forms.ChoiceField(choices=COUNTRY_CHOICES)
    seed_urls = DynamicArrayField(base_field=forms.URLField, required=False, help_text='The URLs you provide in this field will be crawled to find more results.', invalid_message='The element in the position %(nth)s has an invalid URL.')
    fetchers = forms.ModelMultipleChoiceField(widget=Select2Multiple, queryset=Fetcher.objects.filter(is_active=True), required=False)

    error_messages = {
        'incompatibility': 'The use of the fetcher %s is incompatible with the use of the fetcher %s.',
    }

    def clean_fetchers(self):
        # Check if there is an element of the fetchers that is in fetchers.incompatible_with. There probablly is a better way to do this
        fetchers: QuerySet[Fetcher] = self.cleaned_data["fetchers"]
        for fetcher in fetchers:
            incompatible_fetchers = fetcher.incompatible_with.filter(is_active=True)
            for incompatible_fetcher in incompatible_fetchers:
                if incompatible_fetcher in fetchers:
                    raise ValidationError(self.error_messages['incompatibility'], params=(fetcher, incompatible_fetcher), code='incompatibility')
        return fetchers

    class Meta:
        model = AdvancedConfiguration
        fields = ['country_of_search', 'seed_urls', 'fetchers', 'yield_after_gathering_data']


class PostProcessingConfigurationForm(forms.ModelForm):
    post_processors = forms.ModelMultipleChoiceField(queryset=PostProcessor.objects.filter(is_active=True), required=False)

    class Meta:
        model = AdvancedConfiguration
        fields = ['post_processors']


class FilteringConfigurationForm(forms.ModelForm):
    filters = forms.ModelMultipleChoiceField(queryset=Filter.objects.filter(is_active=True, is_builtin=False), required=False)
    start_date = forms.DateTimeField(widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M:%S', attrs={'type': 'datetime-local'}), required=False)
    end_date = forms.DateTimeField(widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M:%S', attrs={'type': 'datetime-local'}), required=False)
    location = forms.CharField(widget=TextInputWithMap(), required=False)

    error_messages = {
        'date_greater_than_now': 'The selected dates must be past dates.',
        'date_invalid_range': 'The start date must be before the end date.',
        # These exceptions should not occur in "normal users", who select values in the map UI.
        'location_bad_format': 'The provided location format cannot be accepted.',
        'latitude_invalid': 'Invalid latitude value.',
        'longitude_invalid': 'Invalid longitude value.',
        'radius_invalid': 'Invalid radius value.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Put coordinates in intial if they exist in the DB
        if self.instance and self.instance.location:
            lat, long = self.instance.location.split(',')
            self.fields['location'].initial = f'{lat},{long},{self.instance.radius}'

    def clean_location(self):
        location = self.cleaned_data['location']
        if location != '' and location is not None:
            splitted = location.split(',')
            if len(splitted) != 3:
                raise ValidationError(self.error_messages['location_bad_format'], code='location_bad_format')
            else:
                lat, long, radius = splitted
                try:
                    lat = float(lat)
                    long = float(long)
                    radius = float(radius)
                except ValueError:
                    raise ValidationError(self.error_messages['location_bad_format'], code='location_bad_format')

                if not (-90 <= lat <= 90):
                    raise ValidationError(self.error_messages['latitude_invalid'], code='latitude_invalid')
                elif not (-180 <= long <= 180):
                    raise ValidationError(self.error_messages['longitude_invalid'], code='longitude_invalid')
                elif not (radius >= 0):
                    raise ValidationError(self.error_messages['radius_invalid'], code='radius_invalid')
        return location

    def clean(self):
        start_date = self.cleaned_data['start_date']
        end_date = self.cleaned_data['end_date']
        now = timezone.now()

        if start_date is not None:
            if start_date > now:
                self.add_error('start_date', self.error_messages['date_greater_than_now'])

        if end_date is not None:
            if end_date > now:
                self.add_error('end_date', self.error_messages['date_greater_than_now'])

        if start_date is not None and end_date is not None:
            if start_date > end_date:  # same condition happens if end_date < start_date
                raise ValidationError(self.error_messages['date_invalid_range'], code='date_invalid_range')

    class Meta:
        model = AdvancedConfiguration
        fields = ['filters', 'strict_filtering', 'start_date', 'end_date']


class ClassificationConfigurationForm(forms.ModelForm):
    classifiers = forms.ModelMultipleChoiceField(queryset=Classifier.objects.filter(is_active=True), required=False)

    class Meta:
        model = AdvancedConfiguration
        fields = ['classifiers']


class ProvidingConfigurationForm(forms.ModelForm):
    class Meta:
        model = AdvancedConfiguration
        fields = ['webhook']
