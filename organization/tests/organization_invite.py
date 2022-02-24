"""
- Can only invite users that haven't been invited to the organization, and aren't in the organization
- Check for invite email
- Check for invite entry in DB
- Cancel invite of user that isn't invited
Remove invite:
- Only owners can remove invite
- Check for remove invite email
- Can't remove invite of a member
- Can't remove invite of a blocked
"""

from http import HTTPStatus
from django.urls import reverse
from .tests_setup import OrganizationTestCase


def create_invite_url(code, invitee, action):
    return f"{reverse('organizations-member-invite', args=[code])}?invitee={invitee}&action={action}"


class OrganizationInviteTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()

    def test_page_name(self):
        self.assertEqual(
            create_invite_url(self.organization.code, self.user_member_encoded_email, 'invite'),
            f"/organizations/{self.organization.code}/members/invite?invitee={self.user_member_encoded_email}&action=invite"
        )

    def test_invite_user_by_anonymous(self):
        response = self.client.get(create_invite_url(self.organization.code, self.user_member_encoded_email, 'invite'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn('login', response.url)

    def test_invite_user_by_non_owner(self):
        self.client.login(email=self.user_member_email, password=self.password)
        response = self.client.get(create_invite_url(self.organization.code, self.user_non_member_encoded_email, 'invite'))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_invite_user_already_invited(self):
        self.user_member_membership.has_accepted = False
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(create_invite_url(self.organization.code, self.user_member_encoded_email, 'invite'))
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_invite_non_existing_user(self):
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(create_invite_url(self.organization.code, 'nonexistingemail@mail.com', 'invite'))
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_invite_user_owner(self):
        self.user_member_membership.is_owner = True
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(create_invite_url(self.organization.code, self.user_member_encoded_email, 'invite'))
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_invite_user_not_invited_wrong_method(self):
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(create_invite_url(self.organization.code, self.user_non_member_encoded_email, 'cancel'))
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_invite_user_not_invited_no_method(self):
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(create_invite_url(self.organization.code, self.user_non_member_encoded_email, ''))
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_invite_user_not_invited(self):
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(create_invite_url(self.organization.code, self.user_non_member_encoded_email, 'invite'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.user_non_member, self.organization.members.all())


class OrganizationInviteCancelTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()

    def test_page_name(self):
        self.assertEqual(
            create_invite_url(self.organization.code, self.user_member_encoded_email, 'cancel'),
            f"/organizations/{self.organization.code}/members/invite?invitee={self.user_member_encoded_email}&action=cancel"
        )

    def test_cancel_invite_user_by_anonymous(self):
        response = self.client.get(create_invite_url(self.organization.code, self.user_member_encoded_email, 'cancel'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn('login', response.url)

    def test_cancel_invite_user_by_non_owner(self):
        self.user_member_membership.has_accepted = False
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)

        response = self.client.get(create_invite_url(self.organization.code, self.user_non_member_email, 'cancel'))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cancel_invite_user_not_invited(self):
        self.user_member_membership.delete()
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(create_invite_url(self.organization.code, self.user_member_encoded_email, 'cancel'))
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_cancel_invite_wrong_method_user_invited(self):
        self.user_member_membership.has_accepted = False
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(create_invite_url(self.organization.code, self.user_member_encoded_email, 'invite'))
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_cancel_invite_user_invited(self):
        self.user_member_membership.has_accepted = False
        self.user_member_membership.save()
        self.client.login(email=self.user_owner_email, password=self.password)

        response = self.client.get(create_invite_url(self.organization.code, self.user_member_encoded_email, 'cancel'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn(self.user_non_member, self.organization.members.all())


class OrganizationAcceptInviteTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('organizations-member-accept_invite', args=[self.organization.code])

    def test_page_name(self):
        self.assertEqual(
            self.url,
            f"/organizations/{self.organization.code}/members/accept_invite"
        )

    def test_accept_invite_user_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn('login', response.url)

    def test_accept_invite_user_non_member(self):
        self.client.login(email=self.user_member_email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_accept_invite_user_already_in_organization(self):
        self.user_member_membership.has_accepted = True
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_accept_invite_user_blocked(self):
        self.user_member_membership.is_blocked = True
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_accept_invite_user_not_in_organization(self):
        self.user_member_membership.has_accepted = False
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.organization.membership_set.get(user=self.user_member).has_accepted, True)


class OrganizationDeclineInviteTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('organizations-member-decline_invite', args=[self.organization.code])

    def test_page_name(self):
        self.assertEqual(
            self.url,
            f"/organizations/{self.organization.code}/members/decline_invite"
        )

    def test_decline_invite_user_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn('login', response.url)

    def test_decline_invite_user_non_member(self):
        self.client.login(email=self.user_member_email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_decline_invite_user_already_in_organization(self):
        self.user_member_membership.has_accepted = True
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_decline_invite_user_blocked(self):
        self.user_member_membership.is_blocked = True
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_decline_invite_user_not_in_organization(self):
        self.user_member_membership.has_accepted = False
        self.user_member_membership.save()
        self.client.login(email=self.user_member_email, password=self.password)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn(self.user_member_membership, self.organization.membership_set.all())


class OrganizationInvitesViewTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(email=self.user_member_email, password=self.password)

    def test_endpoint(self):
        response = self.client.get('/organizations/invites/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Invites", html=True)

    def test_page_name(self):
        self.assertEqual('/organizations/invites/', reverse('organizations-invites'))

    def test_page_template(self):
        response = self.client.get(reverse('organizations-invites'))
        self.assertTemplateUsed(response, template_name='organization/invites_list.html')

    def test_page_invites(self):
        self.user_member_membership.has_accepted = False
        self.user_member_membership.save()

        response = self.client.get(reverse('organizations-invites'))
        self.assertContains(response, self.organization.name, html=True)