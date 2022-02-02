from django.contrib.auth.mixins import UserPassesTestMixin
from ..models import Membership


class UserIsOwner(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        organization_code = self.kwargs.get('code', None)
        return Membership.objects.filter(organization__code=organization_code, user=user, is_owner=True).exists()
