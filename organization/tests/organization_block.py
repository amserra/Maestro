"""
Can't block an owner
Can't block a user that is already blocked
Can't block a user that hasn't accepted the invite yet
Can't block a user that is already blocked
Can't unblock a user tht isn't blocked
"""

from http import HTTPStatus
from django.urls import reverse
from .tests_setup import OrganizationTestCase


class OrganizationBlockTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()

    def test_page_name(self):
        self.assertEqual(f'/organizations/{self.organization.code}/members/{self.user_member_email}/block', reverse('organizations-member-block', args=[self.organization.code, self.user_member_email]))

    def test_block_anonymous_user(self):
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_non_member_encoded_email])}?action=block")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn('login', response.url)

    def test_block_member_by_non_member(self):
        self.client.login(email=self.user_non_member_email, password=self.password)
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=block")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_block_organization_owner_by_member(self):
        self.client.login(email=self.user_member_email, password=self.password)
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_owner_encoded_email])}?action=block")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_block_organization_owner_by_owner(self):
        self.user_member_membership.is_owner = True
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_owner_encoded_email])}?action=block")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_block_blocked_member(self):
        self.user_member_membership.is_blocked = True
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=block")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_block_user_invited(self):
        self.user_member_membership.has_accepted = False
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=block")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_block_organization_member_non_owner_wrong_method(self):
        self.client.login(email=self.user_owner_email, password=self.password)

        self.assertIn(self.user_member, self.organization.members.all())
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=unblock")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_block_organization_member_non_owner(self):
        self.client.login(email=self.user_owner_email, password=self.password)

        self.assertIn(self.user_member, self.organization.members.all())
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=block")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        membership = self.organization.membership_set.get(user__email=self.user_member_email)
        self.assertEqual(membership.is_blocked, True)


class OrganizationUnblockTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()

    def test_unblock_anonymous_user(self):
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_non_member_encoded_email])}?action=unblock")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn('login', response.url)

    def test_unblock_member_by_non_member(self):
        self.client.login(email=self.user_non_member_email, password=self.password)
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=unblock")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_unblock_organization_owner_by_member(self):
        self.client.login(email=self.user_member_email, password=self.password)
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_owner_encoded_email])}?action=unblock")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_unblock_organization_owner_by_owner(self):
        self.user_member_membership.is_owner = True
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_owner_encoded_email])}?action=unblock")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unblock_unblocked_member(self):
        self.user_member_membership.is_blocked = False
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=unblock")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_unblock_user_invited(self):
        self.user_member_membership.has_accepted = False
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=unblock")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unblock_organization_member_non_owner_wrong_method(self):
        self.user_member_membership.is_blocked = True
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)

        self.assertIn(self.user_member, self.organization.members.all())
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=block")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_unblock_organization_member_non_owner_no_method(self):
        self.user_member_membership.is_blocked = True
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)

        self.assertIn(self.user_member, self.organization.members.all())
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_unblock_organization_member_non_owner(self):
        self.user_member_membership.is_blocked = True
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)

        self.assertIn(self.user_member, self.organization.members.all())
        response = self.client.get(f"{reverse('organizations-member-block', args=[self.organization.code, self.user_member_encoded_email])}?action=unblock")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        membership = self.organization.membership_set.get(user__email=self.user_member_email)
        self.assertEqual(membership.is_blocked, False)
