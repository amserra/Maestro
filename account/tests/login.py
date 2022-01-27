from http import HTTPStatus
from django.urls import reverse
from django.test import TestCase
from account.forms import CustomAuthenticationForm
from django.contrib.auth import get_user_model
from account.models import UserManager


class LoginFormTests(TestCase):
    """
    Unit test of the login Form
    """

    def setUp(self):
        self.email = 'test@mail.com'
        self.invalid_email = 'thisisnotanemail'
        self.password = 'anUncommonP@ssword!'
        self.invalid_password = 'password'
        self.user = get_user_model().objects.create_user(email=self.email, password=self.password)

    def test_login_form_valid(self):
        # username instead of email because of custom user model
        form = CustomAuthenticationForm(data={
            'username': self.email,
            'password': self.password
        })
        self.assertTrue(form.is_valid())

    def test_login_form_invalid_email_field(self):
        form = CustomAuthenticationForm(data={
            'username': self.invalid_email,
            'password': self.password
        })
        self.assertTrue(form.errors['username'])
        self.assertFalse(form.is_valid())

    def test_login_form_invalid_password_field(self):
        form = CustomAuthenticationForm(data={
            'username': self.email,
        })
        self.assertTrue(form.errors['password'])
        self.assertFalse(form.is_valid())

    def test_login_form_wrong_email(self):
        form = CustomAuthenticationForm(data={
            'username': self.email + 'x',
            'password': self.password
        })
        self.assertTrue(form.errors['__all__'])
        self.assertFalse(form.is_valid())

    def test_login_form_wrong_password(self):
        form = CustomAuthenticationForm(data={
            'username': self.email,
            'password': self.password + '!'
        })
        self.assertTrue(form.errors['__all__'])
        self.assertFalse(form.is_valid())


class LoginViewTests(TestCase):
    """
    Integration test of the login functionality of the Form and the View
    """

    def setUp(self):
        self.email = 'test@mail.com'
        self.invalid_email = 'thisisnotanemail'
        self.password = 'anUncommonP@ssword!'
        self.invalid_password = 'password'
        self.user = get_user_model().objects.create_user(email=self.email, password=self.password)

    def test_endpoint(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Login to your account", html=True)

    def test_page_name(self):
        response = self.client.get(reverse('login'))
        self.assertEqual('/login/', reverse('login'))

    def test_page_template(self):
        response = self.client.get(reverse('login'))
        self.assertTemplateUsed(response, template_name='account/login.html')

    def test_post_success(self):
        response = self.client.post(reverse('login'), data={
            'username': self.email,
            'password': self.password,
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_error(self):
        response = self.client.post(reverse('login'), data={
            'username': self.email,
            'password': self.password + '!',
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Invalid email/password combination', html=True)


class LoginTest(TestCase):
    """
    Application test of the login functionality, including the behaviour of the DB
    """
    def setUp(self):
        self.email = 'test@mail.com'
        self.invalid_email = 'thisisnotanemail'
        self.password = 'anUncommonP@ssword!'
        self.invalid_password = 'password'
        self.user = get_user_model().objects.create_user(email=self.email, password=self.password)

    def test_login_success(self):
        response = self.client.post(reverse('login'), data={
            'username': self.email,
            'password': self.password,
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_login_fail_user_not_active(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(reverse('login'), data={
            'username': self.email,
            'password': self.password,
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'This account is not active yet. Please check your email', html=True)
