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

from random import choice
from hashlib import md5
import requests
from io import BytesIO

from .tokens import account_activation_token
from django.core.mail import EmailMessage

from common.decorators.login_forbidden import login_forbidden


adjectives = ('adorable', 'adventurous', 'alert', 'alive', 'amused', 'angry', 'attractive', 'beautiful', 'better', 'bewildered', 'black', 'blue', 'blushing', 'bored', 'brainy', 'brave', 'bright', 'busy', 'calm', 'careful', 'cautious', 'charming', 'cheerful', 'clean', 'clear', 'clever', 'cloudy', 'colorful', 'combative', 'comfortable', 'concerned', 'condemned', 'confused', 'cooperative', 'courageous', 'crazy', 'creepy', 'crowded', 'cruel', 'curious', 'cute', 'dangerous', 'dark', 'dead', 'defeated', 'defiant', 'delightful', 'depressed', 'determined', 'different', 'difficult', 'disgusted', 'distinct', 'disturbed', 'dizzy', 'doubtful', 'drab', 'dull', 'eager', 'easy', 'elated', 'elegant', 'embarrassed', 'enchanting', 'encouraging', 'energetic', 'enthusiastic', 'envious', 'evil', 'excited', 'expensive', 'exuberant', 'fair', 'faithful', 'famous', 'fancy', 'fantastic', 'fierce', 'filthy', 'fine', 'foolish', 'fragile', 'frail', 'frantic', 'friendly', 'frightened', 'funny', 'gentle', 'gifted', 'glamorous', 'gleaming', 'glorious', 'good', 'gorgeous', 'graceful', 'grieving', 'grotesque', 'grumpy', 'handsome', 'happy', 'healthy', 'helpful', 'hilarious', 'homeless', 'homely', 'hungry', 'hurt', 'important', 'impossible', 'inexpensive', 'innocent', 'inquisitive', 'itchy', 'jittery', 'jolly', 'joyous', 'kind', 'light', 'lively', 'lonely', 'long', 'lovely', 'lucky', 'magnificent', 'misty', 'modern', 'motionless', 'muddy', 'mushy', 'mysterious', 'nasty', 'naughty', 'nervous', 'nice', 'nutty', 'obedient', 'obnoxious', 'odd', 'old-fashioned', 'open', 'outrageous', 'outstanding', 'panicky', 'perfect', 'plain', 'poised', 'poor', 'powerful', 'precious', 'prickly', 'proud', 'puzzled', 'quaint', 'real', 'relieved', 'repulsive', 'rich', 'scary', 'selfish', 'shiny', 'shy', 'silly', 'sleepy', 'smiling', 'smoggy', 'sore', 'sparkling', 'splendid', 'spotless', 'stormy', 'strange', 'stupid', 'successful', 'super', 'talented', 'tame', 'tender', 'tense', 'testy', 'thankful', 'thoughtful', 'thoughtless', 'tired', 'tough', 'troubled', 'ugliest', 'ugly', 'uninterested', 'unsightly', 'unusual', 'upset', 'uptight', 'vast', 'victorious', 'vivacious', 'wandering', 'weary', 'wicked', 'wide-eyed', 'wild', 'witty', 'worrisome', 'worried', 'wrong', 'zany', 'zealous')
animals = ('alligator', 'ant', 'bear', 'bee', 'bird', 'camel', 'cat', 'cheetah', 'chicken', 'chimpanzee', 'cow', 'crocodile', 'deer', 'dog', 'dolphin', 'duck', 'eagle', 'elephant', 'fish', 'fly', 'fox', 'frog', 'giraffe', 'goat', 'goldfish', 'hamster', 'hippopotamus', 'horse', 'kangaroo', 'kitten', 'lion', 'lobster', 'monkey', 'octopus', 'owl', 'panda', 'pig', 'puppy', 'rabbit', 'rat', 'scorpion', 'seal', 'shark', 'sheep', 'snail', 'snake', 'spider', 'squirrel', 'tiger', 'turtle', 'wolf', 'zebra')


def get_identicon(email, image_format='jpg', size=100):
    email_hash = md5(email.lower().encode('utf-8')).hexdigest()
    url = f'https://www.gravatar.com/avatar/{email_hash}.{image_format}?d=identicon&s={size}'
    response = requests.get(url)
    image_bytes = BytesIO(response.content)
    return email_hash, image_bytes


def get_default_image(email):
    email_hash = md5(email.lower().encode('utf-8')).hexdigest()
    url = finders.find('common/default_avatar.png')
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

        # Handle no first/last name
        if not user.first_name or not user.last_name:
            user.first_name = choice(adjectives)
            user.last_name = choice(animals)

        # Capitalize first letter of first and last names
        user.first_name = user.first_name.title()
        user.last_name = user.last_name.title()

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
        message = f'Hello. An account has been created in Maestro ({current_site}) with this email. To activate the account, please follow the link: \n {activation_link}'
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
    success_message = 'Your profile was updated successfully'

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
