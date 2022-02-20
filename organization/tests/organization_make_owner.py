"""
Only owners can make other users owners
Can't make owner user that is blocked
Can't make owner user that hasn't accepted the invite
"""

from http import HTTPStatus
from django.urls import reverse
from django.utils.http import urlencode
from .tests_setup import OrganizationTestCase


class OrganizationMakeOwnerTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()

    def test_page_name(self):
        self.assertEqual(f'/organizations/{self.organization.code}/members/{self.user_member_email}/make-owner', reverse('organizations-member-make-owner', args=[self.organization.code, self.user_member_email]))

    def test_make_owner_user_not_existent(self):
        encoded_email = urlencode({'email': 'random@mail.com'}).split('=')[1]
        self.client.login(email=self.user_owner_email, password=self.password)
        response = self.client.get(reverse('organizations-member-make-owner', args=[self.organization.code, encoded_email]))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_make_owner_user_not_in_organization(self):
        encoded_email = urlencode({'email': self.user_non_member}).split('=')[1]
        self.client.login(email=self.user_owner_email, password=self.password)
        response = self.client.get(reverse('organizations-member-make-owner', args=[self.organization.code, encoded_email]))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_make_owner_user_blocked(self):
        self.user_member_membership.is_blocked = True
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(reverse('organizations-member-make-owner', args=[self.organization.code, self.user_member_encoded_email]))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_make_owner_user_invite_pending(self):
        self.user_member_membership.has_accepted = False
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(reverse('organizations-member-make-owner', args=[self.organization.code, self.user_member_encoded_email]))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_make_owner_another_owner(self):
        self.user_member_membership.is_owner = True
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(reverse('organizations-member-make-owner', args=[self.organization.code, self.user_member_encoded_email]))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_make_owner_member(self):
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(reverse('organizations-member-make-owner', args=[self.organization.code, self.user_member_encoded_email]))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_make_owner_by_a_non_owner_user(self):
        self.client.login(email=self.user_non_member_email, password=self.password)

        response = self.client.get(reverse('organizations-member-make-owner', args=[self.organization.code, self.user_owner_encoded_email]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_make_owner_by_a_non_owner_member(self):
        self.client.login(email=self.user_member_email, password=self.password)

        response = self.client.get(reverse('organizations-member-make-owner', args=[self.organization.code, self.user_owner_encoded_email]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
