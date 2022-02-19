from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse
from organization.models import Organization
from common.tests import create_user


class OrganizationListViewTests(TestCase):
    def setUp(self):
        create_user()
        self.client.login(email='john_smith@mail.com', password='asmartpassword1')
        Organization.objects.create(code='APA', name='Agencia Portuguesa do Ambiente')

    def test_endpoint(self):
        response = self.client.get('/organizations/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "My organizations", html=True)

    def test_page_name(self):
        self.assertEqual('/organizations/', reverse('organizations-list'))

    def test_page_template(self):
        response = self.client.get(reverse('organizations-list'))
        self.assertTemplateUsed(response, template_name='organization/list.html')
