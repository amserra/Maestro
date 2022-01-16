from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm

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