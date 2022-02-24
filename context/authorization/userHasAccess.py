from django.contrib.auth.mixins import UserPassesTestMixin
from context.helpers import get_user_search_contexts
from context.models import SearchContext
from django.core.exceptions import ObjectDoesNotExist


class UserHasAccess(UserPassesTestMixin):
    """"(For CBV) Checks if the current authenticated user (request.user) is a member of the organization that
    owns the context/is the user that owns the context passed via kwarg 'code'"""
    def test_func(self):
        user = self.request.user
        context_code = self.kwargs.get('code', None)

        try:
            context = SearchContext.objects.get(code=context_code)
            if context.owner_type.name == 'user':
                return True
            else:
                organization = context.owner
                return True if user in organization.active_members else False
        except ObjectDoesNotExist:
            return False
