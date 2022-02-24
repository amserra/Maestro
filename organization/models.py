from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from account.models import User
from context.models import SearchContext


class Organization(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50, blank=False)  # required
    create_date = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, through='Membership')
    members_can_edit = models.BooleanField(default=True)
    members_can_create = models.BooleanField(default=True)

    contexts = GenericRelation(SearchContext, object_id_field='owner_id', content_type_field='owner_type', related_query_name='organization')

    @property
    def active_members(self):
        return self.members.filter(membership__has_accepted=True, membership__is_blocked=False).all()

    @property
    def owners(self):
        return self.members.filter(membership__has_accepted=True, membership__is_blocked=False, membership__is_owner=True).all()

    def user_in_organization(self, user: User) -> bool:
        return self.members.filter(user=user).exists()

    def __str__(self):
        return self.code


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    # Invite
    has_accepted = models.BooleanField(default=False)
    invite_date = models.DateTimeField(auto_now_add=True)
    # Membership
    join_date = models.DateTimeField(null=True)  # starts at null when invite is sent
    is_owner = models.BooleanField(default=False)  # owner instead of admin to disambiguate from platform admin
    is_blocked = models.BooleanField(default=False)  # block is the same as a soft delete

    def __str__(self):
        return f'{self.user} - {self.organization}'
