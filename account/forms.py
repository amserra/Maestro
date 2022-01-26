from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from imagekit.forms import ProcessedImageField
from imagekit.processors import ResizeToFill
from django.contrib.auth.hashers import check_password, make_password, is_password_usable
from django.core.exceptions import ValidationError


class CustomPasswordResetForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label='New password confirmation',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'autofocus': True}))
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    error_messages = {
        'invalid_login': 'Invalid email/password combination',
        'inactive': 'This account is not active yet. Please check your email',
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                try:
                    user_temp = User.objects.get(email=username)
                except User.DoesNotExist:
                    user_temp = None

                if user_temp and user_temp.is_active is False:
                    raise ValidationError(
                        self.error_messages['inactive'],
                        code='inactive',
                    )

                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class UserRegisterForm(UserCreationForm):
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )
    password2 = forms.CharField(
        label='Password confirmation',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )

    error_messages = {
        'missing_first_name': 'Please provide the first name',
        'missing_last_name': 'Please provide the last name',
    }

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        # If there is one name but not the other
        if not first_name and last_name:
            self.add_error('first_name', self.error_messages['missing_first_name'])
        elif first_name and not last_name:
            self.add_error('last_name', self.error_messages['missing_last_name'])

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    error_messages = {
        'missing_old_password': 'Please provide the old password',
        'missing_new_password': 'Please provide the new password',
        'missing_new_password_confirmation': 'Please provide the new password confirmation',
        'new_password_ne_confirmation_password': 'The new password must match the confirmation password',
        'confirmation_password_ne_new_password': 'The confirmation password must match the new password',
        'old_password_ne_password': 'The provided password doesn\'t match the old password',
        'new_password_not_usable': 'The new password you provided can\'t be used. Please provide another',
    }

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
                self.add_error('old_password', self.error_messages['missing_old_password'])
            if not new_password:
                self.add_error('new_password', self.error_messages['missing_new_password'])
            if not new_password_confirmation:
                self.add_error('new_password_confirmation', self.error_messages['missing_new_password_confirmation'])

        if all_filled:
            if new_password != new_password_confirmation:
                self.add_error('new_password', self.error_messages['new_password_ne_confirmation_password'])
                self.add_error('new_password_confirmation', self.error_messages['confirmation_password_ne_new_password'])
            elif not check_password(old_password, self.user.password):
                self.add_error('old_password', self.error_messages['old_password_ne_password'])
            elif not is_password_usable(make_password(new_password)):
                self.add_error('new_password', self.error_messages['new_password_not_usable'])
            else:
                try:
                    validate_password(new_password, self.user)
                except ValidationError:
                    self.add_error('new_password', self.error_messages['new_password_not_usable'])

    class Meta:
        model = User
        fields = ['avatar', 'email', 'first_name', 'last_name']
