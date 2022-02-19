from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from common.tests import create_user
from organization.forms import OrganizationCreateForm
from organization.models import Organization


class OrganizationCreateFormTest(TestCase):
    """
    Unit test of the organization create form
    """
    def setUp(self):
        self.organization_code = 'APA'
        self.organization_name = 'Agencia Portuguesa do Ambiente'

    def test_organization_create_success(self):
        form = OrganizationCreateForm(data={
            'code': self.organization_code,
            'name': self.organization_name
        })
        self.assertTrue(form.is_valid())

    def test_organization_create_invalid_no_code(self):
        form = OrganizationCreateForm(data={
            'name': self.organization_name,
        })
        self.assertFalse(form.is_valid())

    def test_organization_create_invalid_no_name(self):
        form = OrganizationCreateForm(data={
            'code': self.organization_code,
        })
        self.assertFalse(form.is_valid())

    def test_organization_create_invalid_code_big(self):
        form = OrganizationCreateForm(data={
            'code': self.organization_code * 10,
            'name': self.organization_name
        })
        self.assertFalse(form.is_valid())


class OrganizationCreateViewTests(TestCase):
    def setUp(self):
        create_user(email='john_smith@mail.com', password='asmartpassword1')
        self.client.login(email='john_smith@mail.com', password='asmartpassword1')

    def test_endpoint(self):
        response = self.client.get('/organizations/new/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Create", html=True)

    def test_page_name(self):
        self.assertEqual('/organizations/new/', reverse('organizations-new'))

    def test_page_template(self):
        response = self.client.get(reverse('organizations-new'))
        self.assertTemplateUsed(response, template_name='organization/form.html')

    def test_post_success(self):
        response = self.client.post(reverse('organizations-new'), data={
            'code': 'APA',
            'name': 'Associacao Portuguesa do Ambiente',
        })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_error(self):
        response = self.client.post(reverse('organizations-new'), data={
            'code': 'APA',
        })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'This field is required.', html=True)


class OrganizationCreateTest(TestCase):
    def setUp(self):
        create_user(email='john_smith@mail.com', password='asmartpassword1')
        self.client.login(email='john_smith@mail.com', password='asmartpassword1')

    def test_organization_create(self):
        response = self.client.post(reverse('organizations-new'), data={
            'code': 'APA',
            'name': 'Agencia Portuguesa do Ambiente',
        })

        organization = Organization.objects.get(code='APA')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(organization)
        self.assertEqual(organization.membership_set.all().count(), 1)
        self.assertEqual(organization.members_can_edit, True)
        self.assertEqual(organization.members_can_create, True)
