from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from ..models import Membership
from functools import wraps


class UserIsOwner(UserPassesTestMixin):
    """"(For CBV) Checks if the current authenticated user (request.user) is an owner of the organization passed via kwarg 'code'"""
    def test_func(self):
        user = self.request.user
        organization_code = self.kwargs.get('code', None)
        return Membership.objects.filter(organization__code=organization_code, user=user, is_owner=True).exists()


def user_is_owner(function):
    """"(For FBV) Checks if the current authenticated user (request.user) is an owner of the organization passed via kwarg 'code'"""
    @wraps(function)
    def wrap(request, *args, **kwargs):

        user = request.user
        organization_code = kwargs.get('code', None)
        if Membership.objects.filter(organization__code=organization_code, user=user, is_owner=True).exists():
            return function(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    return wrap


class UserIsMember(UserPassesTestMixin):
    """"(For CBV) Checks if the current authenticated user (request.user) is a member of the organization passed via kwarg 'code'"""
    def test_func(self):
        user = self.request.user
        organization_code = self.kwargs.get('code', None)
        return Membership.objects.filter(organization__code=organization_code, user=user, has_accepted=True, is_blocked=False).exists()


def user_is_member(function):
    """"(For FBV) Checks if the current authenticated user (request.user) is a member of the organization passed via kwarg 'code'"""
    @wraps(function)
    def wrap(request, *args, **kwargs):

        user = request.user
        organization_code = kwargs.get('code', None)
        if Membership.objects.filter(organization__code=organization_code, user=user, has_accepted=True, is_blocked=False).exists():
            return function(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    return wrap
