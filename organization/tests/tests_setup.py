from django.test import TestCase
from django.utils.http import urlencode
from organization.models import Organization, Membership
from common.tests import create_user


class OrganizationTestCase(TestCase):
    def setUp(self):
        self.user_non_member_email = 'user1@mail.com'
        self.user_non_member_encoded_email = urlencode({'email': self.user_non_member_email}).split('=')[1]
        self.user_member_email = 'user2@mail.com'
        self.user_member_encoded_email = urlencode({'email': self.user_member_email}).split('=')[1]
        self.user_owner_email = 'user3@mail.com'
        self.user_owner_encoded_email = urlencode({'email': self.user_owner_email}).split('=')[1]
        self.password = 'asmartpassword1'
        # Create users
        self.user_non_member = create_user(email=self.user_non_member_email, password=self.password)
        self.user_member = create_user(email=self.user_member_email, password=self.password)
        self.user_owner = create_user(email=self.user_owner_email, password=self.password)
        # Create organization and memberships
        self.organization = Organization.objects.create(code='APA', name='Agencia Portuguesa do Ambiente')
        self.user_member_membership = Membership.objects.create(user=self.user_member, organization=self.organization, has_accepted=True, is_blocked=False, is_owner=False)
        self.user_owner_membership = Membership.objects.create(user=self.user_owner, organization=self.organization, has_accepted=True, is_blocked=False, is_owner=True)
