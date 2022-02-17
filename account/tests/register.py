from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.test import TestCase
from django.urls import reverse
from account.forms import UserRegisterForm
from django.core import mail


class RegisterFormTests(TestCase):
    """
    Unit test of the register Form
    """

    def setUp(self):
        self.email = 'test@mail.com'
        self.invalid_email = 'thisisnotanemail'
        self.first_name = 'John'
        self.last_name = 'Mckenzie'
        self.password = 'anUncommonP@ssword!'
        self.invalid_password = 'password'

    def test_register_form_valid_with_all(self):
        form = UserRegisterForm(data={
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'password1': self.password,
            'password2': self.password
        })
        self.assertTrue(form.is_valid())

    def test_register_form_valid_without_names(self):
        form = UserRegisterForm(data={
            'email': self.email,
            'password1': self.password,
            'password2': self.password
        })
        self.assertFalse(form.is_valid())

    def test_register_form_invalid_no_email(self):
        form = UserRegisterForm(data={
            'password1': self.password,
            'password2': self.password
        })
        self.assertTrue(form.errors['email'])
        self.assertFalse(form.is_valid())

    def test_register_form_invalid_no_password(self):
        form = UserRegisterForm(data={
            'email': self.email,
        })
        self.assertTrue(form.errors['password1'])
        self.assertTrue(form.errors['password2'])
        self.assertFalse(form.is_valid())

    def test_register_form_invalid_one_password_only(self):
        form = UserRegisterForm(data={
            'email': self.email,
            'password2': self.password
        })
        self.assertTrue(form.errors['password1'])
        self.assertFalse(form.is_valid())

    def test_register_form_invalid_with_invalid_email(self):
        form = UserRegisterForm(data={
            'email': self.invalid_email,
            'password1': self.password,
            'password2': self.password
        })
        self.assertTrue(form.errors['email'])
        self.assertFalse(form.is_valid())

    def test_register_form_invalid_with_weak_password(self):
        form = UserRegisterForm(data={
            'email': self.email,
            'password1': self.invalid_password,
            'password2': self.invalid_password
        })
        self.assertTrue(form.errors['password2'])
        self.assertFalse(form.is_valid())

    def test_register_form_invalid_with_different_passwords(self):
        form = UserRegisterForm(data={
            'email': self.email,
            'password1': self.password,
            'password2': self.password + '!'
        })
        self.assertTrue(form.errors['password2'])
        self.assertFalse(form.is_valid())


class RegisterViewTests(TestCase):
    """
    Integration test of the register functionality of the Form and the View
    """

    def setUp(self):
        self.email = 'test@mail.com'
        self.invalid_email = 'thisisnotanemail'
        self.first_name = 'John'
        self.last_name = 'Mckenzie'
        self.password = 'anUncommonP@ssword!'
        self.invalid_password = 'password'

    def test_endpoint(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Create an account", html=True)

    def test_page_name(self):
        response = self.client.get(reverse('register'))
        self.assertEqual('/register/', reverse('register'))

    def test_page_template(self):
        response = self.client.get(reverse('register'))
        self.assertTemplateUsed(response, template_name='account/register.html')

    def test_post_success(self):
        response = self.client.post(reverse('register'), data={
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'password1': self.password,
            'password2': self.password
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_error(self):
        response = self.client.post(reverse('register'), data={
            'email': self.invalid_email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'password1': self.password,
            'password2': self.password
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Enter a valid email address.', html=True)


class TestUserCreation(TestCase):
    """
    Application test of the register functionality, including the behaviour of the DB
    """
    def setUp(self):
        self.email = 'test@mail.com'
        self.invalid_email = 'thisisnotanemail'
        self.first_name = 'John'
        self.last_name = 'Mckenzie'
        self.password = 'anUncommonP@ssword!'
        self.invalid_password = 'password'

    def test_user_created_full(self):
        # Create user
        user_count_before_creation = get_user_model().objects.count()
        response = self.client.post(reverse('register'), data={
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'password1': self.password,
            'password2': self.password
        })
        user = get_user_model().objects.get(email=self.email)
        users = get_user_model().objects.all()
        # Test fields
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(users.count(), user_count_before_creation + 1)
        self.assertEqual(user.email, self.email)
        self.assertEqual(user.first_name, self.first_name)
        self.assertEqual(user.last_name, self.last_name)
        self.assertTrue(check_password(self.password, user.password))
        # Check if avatar was created
        self.assertTrue(user.avatar)
        # Check if email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Activate your account.')

    def test_user_activation_with_email(self):
        # Create user
        response = self.client.post(reverse('register'), data={
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'password1': self.password,
            'password2': self.password
        })
        user = get_user_model().objects.get(email=self.email)

        # Check is user is not active
        self.assertFalse(user.is_active)
        # Check if email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Activate your account.')
        # Get email link
        link = mail.outbox[0].body.splitlines()[1]
        response = self.client.get(link, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

