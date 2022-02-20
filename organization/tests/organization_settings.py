from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse
from common.tests import create_user
from organization.forms import OrganizationSettingsForm
from organization.models import Organization, Membership


class OrganizationSettingsFormTest(TestCase):
    """
    Unit test of the organization update form
    """
    def setUp(self):
        self.organization_code = 'APA'
        self.organization_name = 'Agencia Portuguesa do Ambiente'
        self.organization = Organization.objects.create(code=self.organization_code, name=self.organization_name)

    def test_organization_update_success(self):
        form = OrganizationSettingsForm(data={
            'code': self.organization_code,
            'name': self.organization_name,
            'members_can_create': False,
            'members_can_edit': True,
        })
        self.assertTrue(form.is_valid())

    def test_organization_update_invalid_code_big(self):
        form = OrganizationSettingsForm(data={
            'name': self.organization_code * 100,
        })
        self.assertFalse(form.is_valid())


class OrganizationUpdateViewTests(TestCase):
    def setUp(self):
        self.organization_code = 'APA'
        self.organization_name = 'Agencia Portuguesa do Ambiente'
        self.organization = Organization.objects.create(code=self.organization_code, name=self.organization_name)
        self.user = create_user(email='john_smith@mail.com', password='asmartpassword1')
        self.client.login(email='john_smith@mail.com', password='asmartpassword1')

    def test_page_name(self):
        self.assertEqual(f'/organizations/{self.organization_code}/settings/', reverse('organizations-settings', args=[self.organization_code]))

    def test_page_template(self):
        Membership.objects.create(user=self.user, organization=self.organization, has_accepted=True, is_owner=True)
        response = self.client.get(reverse('organizations-settings', args=[self.organization_code]))
        self.assertTemplateUsed(response, template_name='organization/form.html')

    def test_endpoint_unauthenticated(self):
        response = self.client.get(reverse('organizations-settings', args=[self.organization_code]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_endpoint_authenticated_member(self):
        Membership.objects.create(user=self.user, organization=self.organization, has_accepted=True)
        response = self.client.get(reverse('organizations-settings', args=[self.organization_code]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_endpoint_authenticated_owner(self):
        Membership.objects.create(user=self.user, organization=self.organization, has_accepted=True, is_owner=True)
        response = self.client.get(reverse('organizations-settings', args=[self.organization_code]))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Update", html=True)

    def test_post_success(self):
        Membership.objects.create(user=self.user, organization=self.organization, has_accepted=True, is_owner=True)
        response = self.client.post(reverse('organizations-settings', args=[self.organization_code]), data={
            'code': 'APAX',
            'name': 'Associacao Portuguesa do AmbienteX',
        })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_error(self):
        Membership.objects.create(user=self.user, organization=self.organization, has_accepted=True, is_owner=True)
        response = self.client.post(reverse('organizations-settings', args=[self.organization_code]), data={
            'code': self.organization_code * 10,
        })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'This field is required.', html=True)


class OrganizationSettingsTest(TestCase):
    def setUp(self):
        self.organization_code = 'APA'
        self.organization_name = 'Agencia Portuguesa do Ambiente'
        self.organization = Organization.objects.create(code=self.organization_code, name=self.organization_name)
        self.user = create_user(email='john_smith@mail.com', password='asmartpassword1')
        Membership.objects.create(user=self.user, organization=self.organization, has_accepted=True, is_owner=True)
        self.client.login(email='john_smith@mail.com', password='asmartpassword1')

    def test_organization_update(self):
        code = 'APAX'
        name = 'Agencia Portuguesa dos Ambientes'
        response = self.client.post(reverse('organizations-settings', args=[self.organization_code]), data={
            'code': code,
            'name': name,
            'members_can_edit': False,
            'members_can_create': False,
        })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Code doesnt change!
        self.assertFalse(Organization.objects.filter(code=code).exists())

        organization = Organization.objects.get(code=self.organization_code)
        self.assertTrue(organization)
        self.assertEqual(organization.code, self.organization_code)
        self.assertEqual(organization.name, name)
        self.assertEqual(organization.members_can_edit, False)
        self.assertEqual(organization.members_can_create, False)
