from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .models import User
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, View
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, render, redirect
from .forms import ProfileUpdateForm, UserRegisterForm
from django.contrib.staticfiles import finders
from hashlib import md5
import requests
from io import BytesIO
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from common.decorators.login_forbidden import login_forbidden


def get_identicon(email, image_format='jpg', size=100):
    email_hash = md5(email.lower().encode('utf-8')).hexdigest()
    url = f'https://www.gravatar.com/avatar/{email_hash}.{image_format}?d=identicon&s={size}'
    response = requests.get(url)
    image_bytes = BytesIO(response.content)
    return email_hash, image_bytes


def get_default_image(email):
    email_hash = md5(email.lower().encode('utf-8')).hexdigest()
    url = finders.find('organization/default_avatar.png')
    with open(url, "rb") as fp:
        image_bytes = BytesIO(fp.read())
        return email_hash, image_bytes


@method_decorator(login_forbidden, name='dispatch')
class SignupView(SuccessMessageMixin, CreateView):
    template_name = 'account/register.html'
    success_url = reverse_lazy('login')
    form_class = UserRegisterForm
    success_message = 'Profile created successfully. Check your email to confirm the account.'

    def form_valid(self, form):
        user = form.save(commit=False)

        # Provide initial avatar image
        try:
            filename, image = get_identicon(user.email)
        except requests.exceptions.RequestException:
            # If the identicon service is unavailable
            filename, image = get_default_image(user.email)

        user.avatar.save(filename, image, True)

        # Mark user as not active (hasn't confirmed the email) and save
        user.is_active = False
        user.save()
        # Send email for validation
        mail_subject = 'Activate your account.'
        current_site = get_current_site(self.request)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activation_link = f'{current_site}/activate/{uid}/{token}'
        message = f'Hello. An account has been created in Maestro ({current_site}) with this email. To activate the account, please follow the link: \nhttp://{activation_link}'
        to_email = form.cleaned_data.get('email')
        email = EmailMessage(mail_subject, message, to=[to_email])
        email.send()

        return super().form_valid(form)


@method_decorator(login_forbidden, name='dispatch')
class ActivateUserView(SuccessMessageMixin, View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            # activate user and login:
            user.is_active = True
            user.save()
            login(request, user)

            return render(request, 'account/activation_success.html')

        else:
            return render(request, 'account/activation_fail.html')


class ProfileView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    template_name = 'account/profile.html'
    success_url = reverse_lazy('profile')
    model = User
    form_class = ProfileUpdateForm
    success_message = 'Your profile was updated successfully.'

    def get_form_kwargs(self):
        kwargs = super(ProfileView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_object(self):
        return get_object_or_404(User, pk=self.request.user.id)

    def form_valid(self, form):
        user = form.save(commit=False)
        new_password = form.cleaned_data['new_password']
        if new_password:
            user.set_password(new_password)

        user.save()
        # Updating the password logs out all other sessions for the user except the current one.
        update_session_auth_hash(self.request, user)
        return super().form_valid(form)
