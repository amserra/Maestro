from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.auth.hashers import check_password


# No need to test form - the one provided by Django is used, thus we assume it is tested

class PasswordRecoverViewsTests(TestCase):
    """
    Integration test of the password recover (request and request done) functionality of the Form and the View
    """

    def setUp(self):
        self.email = 'test@mail.com'
        self.invalid_email = 'thisisnotanemail'

    def test_endpoint_request(self):
        response = self.client.get('/password_reset/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Reset your password", html=True)

    def test_page_name_request(self):
        self.assertEqual('/password_reset/', reverse('password_reset'))

    def test_page_name_request_done(self):
        self.assertEqual('/password_reset/done/', reverse('password_reset_done'))

    def test_page_name_reset_complete(self):
        self.assertEqual('/reset/done/', reverse('password_reset_complete'))

    def test_page_template_request(self):
        response = self.client.get(reverse('password_reset'))
        self.assertTemplateUsed(response, template_name='account/password_reset.html')

    def test_post_success(self):
        response = self.client.post(reverse('password_reset'), data={
            'email': self.email,
        }, follow=True)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Check if we were sent to password_reset/done
        self.assertEqual(response.wsgi_request.path, '/password_reset/done/')
        self.assertTemplateUsed(response, template_name='account/password_reset_done.html')

    def test_post_error(self):
        response = self.client.post(reverse('password_reset'), data={
            'email': self.invalid_email,
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Enter a valid email address.', html=True)


class TestPasswordReset(TestCase):
    """
    Application test of the password reset functionality, including the behaviour of the DB
    """
    def setUp(self):
        self.email = 'test@mail.com'
        self.old_password = 'theOldP@ssword.'
        self.new_password = 'anUncommonP@ssword!'
        self.user = get_user_model().objects.create_user(email=self.email, password=self.old_password)
        self.response = self.client.post(reverse('password_reset'), data={
            'email': self.email,
        })

    def test_password_reset_email_sent(self):
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password reset', mail.outbox[0].subject)

    def test_password_reset_email_open_link(self):
        link = mail.outbox[0].body.splitlines()[5]
        # follow is used because there is a redirect after the link is clicked
        response = self.client.get(link, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_reset_email_change_password(self):
        link = mail.outbox[0].body.splitlines()[5]
        # follow is used because there is a redirect after the link is clicked
        response = self.client.get(link, follow=True)
        response = self.client.post(response.wsgi_request.path, data={
            'new_password1': self.new_password,
            'new_password2': self.new_password
        }, follow=True)
        user = get_user_model().objects.get(email=self.email)
        self.assertTrue(check_password(self.new_password, user.password))
        # Check if we are redirected to reset/done
        self.assertEqual(response.wsgi_request.path, '/reset/done/')
        self.assertTemplateUsed(response, template_name='account/password_reset_complete.html')
