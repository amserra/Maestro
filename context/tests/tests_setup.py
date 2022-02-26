from django.test import TestCase
from django.utils.http import urlencode

from context.models import SearchContext
from organization.models import Organization, Membership
from common.tests import create_user


class ContextTestCase(TestCase):
    def setUp(self):
        self.context_name = 'Search for images'
        self.context_code = 'search-for-audio'
        self.user_email = 'user1@mail.com'
        self.other_user_email = 'user2@mail.com'
        self.password = 'asmartpassword1'
        # Create users
        self.user = create_user(email=self.user_email, password=self.password)
        self.other_user = create_user(email=self.other_user_email, password=self.password)
        # Create organization and memberships
        self.organization = Organization.objects.create(code='APA', name='Agencia Portuguesa do Ambiente')
        # self.user_member_membership = Membership.objects.create(user=self.user_member, organization=self.organization, has_accepted=True, is_blocked=False, is_owner=False)
        self.context = SearchContext.objects.create(name='search for audio', code=self.context_code, owner=self.user)

