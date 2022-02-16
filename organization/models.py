from django.db import models
from account.models import User


class Organization(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50, blank=False)  # required
    create_date = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, through='Membership')
    members_can_edit = models.BooleanField(default=True)
    members_can_create = models.BooleanField(default=True)

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
