from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden

from context.helpers import get_user_search_contexts
from context.models import SearchContext
from django.core.exceptions import ObjectDoesNotExist
from functools import wraps


class UserCanEdit(UserPassesTestMixin):
    """"(For CBV) Checks if the current authenticated user (request.user) is a member of the organization that
    owns the context AND it can edit/is the user that owns the context passed via kwarg 'code'"""
    def test_func(self):
        user = self.request.user
        context_code = self.kwargs.get('code', None)

        try:
            context = SearchContext.objects.get(code=context_code)
            if context.owner_type.name == 'user':
                return True if context.owner == user else False
            else:
                organization = context.owner
                return True if (user in organization.owners) or (user in organization.active_members and organization.members_can_edit is True) else False
        except ObjectDoesNotExist:
            return False


def user_can_edit(function):
    """"(For FBV) Checks if the current authenticated user (request.user) is a member of the organization that
    owns the context AND it can edit/is the user that owns the context passed via kwarg 'code'"""
    @wraps(function)
    def wrap(request, *args, **kwargs):

        user = request.user
        organization_code = kwargs.get('code', None)

        try:
            context = SearchContext.objects.get(code=organization_code)
            if context.owner_type.name == 'user':
                return function(request, *args, **kwargs) if context.owner == user else HttpResponseForbidden()
            else:
                organization = context.owner
                return function(request, *args, **kwargs) if (user in organization.owners) or (user in organization.active_members and organization.members_can_edit is True) else HttpResponseForbidden()
        except ObjectDoesNotExist:
            return HttpResponseForbidden()

    return wrap
