from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse


class TestPages(TestCase):
    """
    Checks if the pages URLs are working, have the correct names and are using the intended template
    """
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual('/', reverse('home'))
        self.assertTemplateUsed(response, template_name='organization/home.html')
        # self.assertContains(response, "", html=True)

    def test_about_page(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual('/about/', reverse('about'))
        self.assertTemplateUsed(response, template_name='organization/about.html')
        # self.assertContains(response, "", html=True)

    def test_roadmap_page(self):
        response = self.client.get('/roadmap/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual('/roadmap/', reverse('roadmap'))
        self.assertTemplateUsed(response, template_name='organization/roadmap.html')
        # self.assertContains(response, "", html=True)

