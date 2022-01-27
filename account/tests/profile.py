from http import HTTPStatus
from django.urls import reverse
from django.test import TestCase
from account.forms import ProfileUpdateForm
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password


class ProfileFormTests(TestCase):
    """
    Unit test of the profile Form
    """

    def setUp(self):
        self.email = 'test@mail.com'
        self.invalid_email = 'thisisnotanemail'
        self.first_name = 'John'
        self.last_name = 'Steward'
        self.password = 'anUncommonP@ssword!'
        self.new_password = 'anUncommonP@ssword!'
        self.invalid_password = 'password'
        # Create user
        self.client.post(reverse('register'), data={
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'password1': self.password,
            'password2': self.password
        })
        user = get_user_model().objects.get(email=self.email)
        user.is_active = True
        user.save()
        self.user = user
        self.client.login(email=self.email, password=self.password)

    def test_profile_update_email(self):
        # User cant update email in profile update
        form = ProfileUpdateForm(data={
            'email': self.user.email + 'x',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], '')

    def test_profile_update_names(self):
        form = ProfileUpdateForm(data={
            'first_name': self.first_name,
            'last_name': self.last_name
        })
        self.assertTrue(form.is_valid())

    def test_profile_invalid_only_one_password_in_old(self):
        form = ProfileUpdateForm(data={
            'old_password': self.password,
        })
        self.assertTrue(form.errors['new_password'])
        self.assertTrue(form.errors['new_password_confirmation'])
        self.assertFalse(form.is_valid())

    def test_profile_invalid_only_one_password_in_new(self):
        form = ProfileUpdateForm(data={
            'new_password': self.password,
        })
        self.assertTrue(form.errors['old_password'])
        self.assertTrue(form.errors['new_password_confirmation'])
        self.assertFalse(form.is_valid())

    def test_profile_invalid_only_one_password_in_new_confirm(self):
        form = ProfileUpdateForm(data={
            'new_password_confirmation': self.password,
        })
        self.assertTrue(form.errors['new_password'])
        self.assertTrue(form.errors['old_password'])
        self.assertFalse(form.is_valid())

    def test_profile_invalid_only_two_passwords_old_and_new(self):
        form = ProfileUpdateForm(data={
            'old_password': self.password,
            'new_password': self.password,
        })
        self.assertTrue(form.errors['new_password_confirmation'])
        self.assertFalse(form.is_valid())

    def test_profile_invalid_only_two_passwords_old_and_new_confirm(self):
        form = ProfileUpdateForm(data={
            'old_password': self.password,
            'new_password_confirmation': self.password,
        })
        self.assertTrue(form.errors['new_password'])
        self.assertFalse(form.is_valid())

    def test_profile_invalid_only_two_passwords_new_and_new_confirm(self):
        form = ProfileUpdateForm(data={
            'new_password': self.password,
            'new_password_confirmation': self.password,
        })
        self.assertTrue(form.errors['old_password'])
        self.assertFalse(form.is_valid())

    def test_profile_invalid_old_password(self):
        form = ProfileUpdateForm(data={
            'old_password': self.invalid_password,
            'new_password': self.password,
            'new_password_confirmation': self.password,
        }, user=self.user)
        self.assertTrue(form.errors['old_password'])
        self.assertFalse(form.is_valid())

    def test_profile_invalid_new_passwords_mismatch(self):
        form = ProfileUpdateForm(data={
            'old_password': self.password,
            'new_password': self.new_password,
            'new_password_confirmation': self.new_password + '!',
        }, user=self.user)
        self.assertTrue(form.errors['new_password'])
        self.assertTrue(form.errors['new_password_confirmation'])
        self.assertFalse(form.is_valid())

    def test_profile_invalid_weak_new_password(self):
        form = ProfileUpdateForm(data={
            'old_password': self.password,
            'new_password': self.invalid_password,
            'new_password_confirmation': self.invalid_password,
        }, user=self.user)
        self.assertTrue(form.errors['new_password'])
        self.assertTrue(form.errors['new_password_confirmation'])
        self.assertFalse(form.is_valid())

    def test_profile_valid_new_password(self):
        form = ProfileUpdateForm(data={
            'old_password': self.password,
            'new_password': self.new_password,
            'new_password_confirmation': self.new_password,
        }, user=self.user)
        self.assertTrue(form.is_valid())


class ProfileViewTests(TestCase):
    """
    Integration test of the profile functionality of the Form and the View
    """

    def setUp(self):
        self.email = 'test@mail.com'
        self.invalid_email = 'thisisnotanemail'
        self.first_name = 'John'
        self.last_name = 'Steward'
        self.password = 'anUncommonP@ssword!'
        self.new_password = 'anUncommonP@ssword!'
        self.invalid_password = 'password'
        # Create user
        self.client.post(reverse('register'), data={
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'password1': self.password,
            'password2': self.password
        })
        user = get_user_model().objects.get(email=self.email)
        user.is_active = True
        user.save()
        self.user = user
        self.client.login(email=self.email, password=self.password)

    def test_endpoint(self):
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Profile", html=True)

    def test_page_name(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual('/profile/', reverse('profile'))

    def test_page_template(self):
        response = self.client.get(reverse('profile'))
        self.assertTemplateUsed(response, template_name='account/profile.html')

    def test_post_success(self):
        response = self.client.post(reverse('profile'), data={
            'first_name': self.first_name,
            'last_name': self.last_name,
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_error(self):
        response = self.client.post(reverse('profile'), data={
            'old_password': self.password,
            'new_password': self.invalid_password,
            'new_password_confirmation': self.invalid_password,
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'The new password you provided can\'t be used. Please provide another', html=True)


class ProfileUpdateTest(TestCase):
    """
    Application test of the profile functionality, including the behaviour of the DB
    """
    def setUp(self):
        self.email = 'test@mail.com'
        self.invalid_email = 'thisisnotanemail'
        self.first_name = 'John'
        self.last_name = 'Steward'
        self.password = 'anUncommonP@ssword!'
        self.new_password = 'anUncommonP@ssword!'
        self.invalid_password = 'password'
        # Create user
        self.client.post(reverse('register'), data={
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'password1': self.password,
            'password2': self.password
        })
        user = get_user_model().objects.get(email=self.email)
        user.is_active = True
        user.save()
        self.user = user
        self.client.login(email=self.email, password=self.password)

    def test_profile_info_update_success(self):
        response = self.client.post(reverse('profile'), data={
            'first_name': self.first_name,
            'last_name': self.last_name,
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.wsgi_request.user.first_name, self.first_name)
        self.assertEqual(response.wsgi_request.user.last_name, self.last_name)

    def test_profile_password_update_success(self):
        response = self.client.post(reverse('profile'), data={
            'old_password': self.password,
            'new_password': self.new_password,
            'new_password_confirmation': self.new_password,
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(check_password(self.new_password, response.wsgi_request.user.password))
