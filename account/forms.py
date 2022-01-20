from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import User
from django.contrib.auth.forms import UserCreationForm
from imagekit.forms import ProcessedImageField
from imagekit.processors import ResizeToFill
from django.contrib.auth.hashers import check_password, make_password, is_password_usable
from django.core.exceptions import ValidationError


class UserRegisterForm(UserCreationForm):

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        # If there is one name but not the other
        if not first_name and last_name:
            self.add_error('first_name', 'Please provide the first name')
        elif first_name and not last_name:
            self.add_error('last_name', 'Please provide the last name')

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):

    avatar = ProcessedImageField(spec_id='account:user:avatar', processors=[ResizeToFill(100, 100)], format='JPEG')
    email = forms.EmailField(widget=forms.EmailInput(attrs={'readonly': 'readonly'}))
    old_password = forms.CharField(widget=forms.PasswordInput, required=False)
    new_password = forms.CharField(widget=forms.PasswordInput, required=False)
    new_password_confirmation = forms.CharField(widget=forms.PasswordInput, required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password = cleaned_data.get('new_password')
        new_password_confirmation = cleaned_data.get('new_password_confirmation')

        at_least_one_filled = old_password or new_password or new_password_confirmation
        all_filled = old_password and new_password and new_password_confirmation
        if at_least_one_filled:
            if not old_password:
                self.add_error('old_password', 'Please enter the old password')
            if not new_password:
                self.add_error('new_password', 'Please enter the new password')
            if not new_password_confirmation:
                self.add_error('new_password_confirmation', 'Please confirm the new password')

        if all_filled:
            if new_password != new_password_confirmation:
                self.add_error('new_password', 'The new password must match the confirmation password')
                self.add_error('new_password_confirmation', 'The confirmation password must match the new password')
            elif not check_password(old_password, self.user.password):
                self.add_error('old_password', 'The provided password doesn\'t match the old password')
            elif not is_password_usable(make_password(new_password)):
                self.add_error('new_password', 'The new password you provided can\'t be used. Please provide another')
            else:
                try:
                    validate_password(new_password, self.user)
                except ValidationError:
                    self.add_error('new_password', 'The new password you provided can\'t be used. Please provide another')

    class Meta:
        model = User
        fields = ['avatar', 'email', 'first_name', 'last_name']
