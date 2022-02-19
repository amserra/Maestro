from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.templatetags.static import static


def create_user(email='john_smith@mail.com', first_name='John', last_name='Smith', password='asmartpassword1', avatar=static('common/default_avatar.png')):
    user = get_user_model().objects.create_user(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password,
        avatar=avatar
    )
    user.is_active = True
    user.save()
    return user


class TestPages(TestCase):
    """
    Checks if the pages URLs are working, have the correct names and are using the intended template
    """
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual('/', reverse('home'))
        self.assertTemplateUsed(response, template_name='common/home.html')
        # self.assertContains(response, "", html=True)

    def test_about_page(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual('/about/', reverse('about'))
        self.assertTemplateUsed(response, template_name='common/about.html')
        # self.assertContains(response, "", html=True)

    def test_roadmap_page(self):
        response = self.client.get('/roadmap/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual('/roadmap/', reverse('roadmap'))
        self.assertTemplateUsed(response, template_name='common/roadmap.html')
        # self.assertContains(response, "", html=True)

