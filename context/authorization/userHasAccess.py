from django.contrib.auth.mixins import UserPassesTestMixin
from context.helpers import get_user_search_contexts


class UserHasAccess(UserPassesTestMixin):
    """"(For CBV) Checks if the current authenticated user (request.user) is a member of the organization that
    owns the context/is the user that owns the context passed via kwarg 'code'"""
    def test_func(self):
        user = self.request.user
        context_code = self.kwargs.get('code', None)

        contexts = get_user_search_contexts(user)
        return contexts.filter(code=context_code).exists()
