from http import HTTPStatus
from django.urls import reverse
from organization.models import Organization, Membership
from .tests_setup import OrganizationTestCase


class OrganizationLeaveTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()

    def test_leave_organization_anonymous_user(self):
        response = self.client.get(reverse('organizations-leave', args=[self.organization.code]))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn('login', response.url)

    def test_leave_organization_non_member_user(self):
        self.client.login(email=self.user_non_member_email, password=self.password)
        response = self.client.get(reverse('organizations-leave', args=[self.organization.code]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_leave_organization_member_non_owner(self):
        self.client.login(email=self.user_member, password=self.password)

        self.assertIn(self.user_member, self.organization.members.all())
        response = self.client.get(reverse('organizations-leave', args=[self.organization.code]))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn(self.user_member, self.organization.members.all())

    def test_leave_organization_only_owner_and_only_user(self):
        """When the user is the only owner and the only user, they should be able to leave the organization and as side effect the organization is deleted"""
        Membership.objects.get(user=self.user_member, organization=self.organization).delete()
        self.client.login(email=self.user_owner, password=self.password)

        self.assertEqual(self.organization.members.count(), 1)
        response = self.client.get(reverse('organizations-leave', args=[self.organization.code]))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Membership.objects.filter(organization=self.organization, user=self.user_owner).exists())
        self.assertFalse(Organization.objects.filter(code=self.organization.code).exists())

    def test_leave_organization_only_owner_and_not_only_user(self):
        """When the user is the only owner and NOT the only user, they should make another user owner before"""
        self.client.login(email=self.user_owner, password=self.password)

        self.assertEqual(self.organization.members.count(), 2)
        response = self.client.get(reverse('organizations-leave', args=[self.organization.code]))
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_leave_organization_multiple_owners(self):
        """An owner can leave if there is another owner left"""
        self.client.login(email=self.user_owner, password=self.password)
        new_owner = Membership.objects.get(user=self.user_member, organization=self.organization)
        new_owner.is_owner = True
        new_owner.save()

        self.assertEqual(self.organization.members.count(), 2)
        self.assertEqual(self.organization.owners.count(), 2)
        response = self.client.get(reverse('organizations-leave', args=[self.organization.code]))
        self.assertEqual(response.status_code, HTTPStatus.OK)