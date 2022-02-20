from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse
from organization.models import Organization, Membership
from common.tests import create_user
from .tests_setup import OrganizationTestCase


class OrganizationMembersViewTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()

    def test_endpoint_and_page_name(self):
        self.client.login(email=self.user_member_email, password=self.password)
        response = self.client.get(f'/organizations/{self.organization.code}/members/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(f'/organizations/{self.organization.code}/members/', reverse('organizations-member-list', args=[self.organization.code]))
        self.assertTemplateUsed(response, template_name='organization/members_list.html')

    def test_organization_members_non_member(self):
        self.client.login(email=self.user_non_member_email, password=self.password)
        response = self.client.get(f'/organizations/{self.organization.code}/members/')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_organization_members_blocked(self):
        self.user_member_membership.is_blocked = True
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)

        response = self.client.get(f'/organizations/{self.organization.code}/members/')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class OrganizationUserProfileViewTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()

    def test_endpoint_and_page_name(self):
        self.client.login(email=self.user_member_email, password=self.password)
        response = self.client.get(f'/organizations/{self.organization.code}/members/{self.user_member_encoded_email}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(f'/organizations/{self.organization.code}/members/{self.user_member_email}/', reverse('organizations-member-profile', args=[self.organization.code, self.user_member_email]))
        self.assertTemplateUsed(response, template_name='organization/member_profile.html')

    def test_organization_user_profile_non_member(self):
        self.client.login(email=self.user_non_member_email, password=self.password)
        response = self.client.get(f'/organizations/{self.organization.code}/members/{self.user_member_encoded_email}/')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_organization_user_profile_blocked(self):
        self.user_member_membership.is_blocked = True
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)

        response = self.client.get(f'/organizations/{self.organization.code}/members/{self.user_member_encoded_email}/')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
