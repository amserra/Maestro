from urllib.parse import unquote
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, reverse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.utils import timezone as tz
from django.contrib import messages
from common.mixins import SafePaginationMixin, TitleMixin
from .authorization import UserIsOwner, UserIsMember, user_is_owner, user_is_member
from .forms import OrganizationCreateForm, OrganizationSettingsForm, MembershipInviteForm
from .models import Organization, Membership
from account.models import User
from django.core.mail import EmailMessage
from django.utils.timezone import now


class OrganizationListView(LoginRequiredMixin, SafePaginationMixin, ListView):
    template_name = 'organization/list.html'
    context_object_name = 'organizations'
    paginate_by = 5

    def get_queryset(self):
        return self.request.user.organization_set.filter(membership__has_accepted=True, membership__is_blocked=False).order_by('id')

    def get_context_data(self, *args, **kwargs):
        context = super(OrganizationListView, self).get_context_data(*args, **kwargs)
        # Organizations where the user is owner
        organizations_user_owner = Organization.objects.filter(membership__user=self.request.user, membership__is_owner=True)
        context['organizations_user_owner'] = organizations_user_owner
        return context


class OrganizationCreateView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, CreateView):
    title = 'Create an organization'
    template_name = 'organization/form.html'
    success_url = reverse_lazy('organizations-list')
    model = Organization
    form_class = OrganizationCreateForm
    success_message = 'Your have created a new organization'

    def form_valid(self, form):
        organization = form.save()
        # Create membership object for the user creating the organization, and assign him as accepted and owner
        Membership.objects.create(user=self.request.user, organization=organization, has_accepted=True, join_date=tz.now(), is_owner=True)
        return super().form_valid(form)


class OrganizationInvitesView(LoginRequiredMixin, SafePaginationMixin, ListView):
    template_name = 'organization/invites_list.html'
    context_object_name = 'invites'
    paginate_by = 5

    def get_queryset(self):
        return Membership.objects.filter(user=self.request.user, has_accepted=False).order_by('invite_date')


class OrganizationSettingsView(LoginRequiredMixin, UserIsOwner, TitleMixin, SuccessMessageMixin, UpdateView):
    title = 'Update organization %s settings'
    template_name = 'organization/form.html'
    success_url = reverse_lazy('organizations-list')
    model = Organization
    form_class = OrganizationSettingsForm
    slug_field = 'code'
    slug_url_kwarg = 'code'
    success_message = 'Your have updated the organization\'s settings'


# Tests:
# - User that is not in the organization: can he see the contents of it?
# - User that is in the organization: can he see the contents of it?
class OrganizationDetailView(LoginRequiredMixin, UserIsMember, DetailView):
    template_name = 'organization/detail.html'
    model = Organization
    slug_field = 'code'
    slug_url_kwarg = 'code'
    context_object_name = 'organization'


# Any user that is member of the organization can see who else is member
class OrganizationMembersView(LoginRequiredMixin, UserIsMember, SafePaginationMixin, ListView):
    template_name = 'organization/members_list.html'
    context_object_name = 'members'
    paginate_by = 5

    def get_queryset(self):
        # Put users that haven't accepted yet on top (only visible for owners). Users that are not owners only see the accepted
        return Membership.objects.filter(organization__code=self.kwargs['code']).order_by('-has_accepted').order_by('-id')

    def get_context_data(self, *args, **kwargs):
        context = super(OrganizationMembersView, self).get_context_data(*args, **kwargs)
        organization = Organization.objects.get(code=self.kwargs['code'])
        context['organization'] = organization
        context['invite_form'] = MembershipInviteForm(code=organization.code)
        # Tells if user is organization's owner
        context['is_owner'] = Membership.objects.filter(organization=organization, user=self.request.user, is_owner=True).exists()
        return context


class OrganizationUserProfileView(LoginRequiredMixin, UserIsMember, DetailView):
    template_name = 'organization/member_profile.html'
    model = Membership
    context_object_name = 'member'

    def get_object(self):
        return get_object_or_404(Membership, organization__code=self.kwargs['code'], user__email=unquote(self.kwargs['user_email']))


@login_required
@user_is_owner
def organization_invite_member(request, code):
    organization = get_object_or_404(Organization, code=code)
    invitee = request.GET.get('invitee', None)
    invitee_user = get_object_or_404(User, email=invitee)
    if invitee_user in organization.members.all():
        messages.error(request, "The user is already invited or is already in the organization")
        return HttpResponseBadRequest()
    else:
        Membership.objects.create(organization=organization, user=invitee_user).save()
        # Send email
        mail_subject = 'Organization invite pending'
        url = request.build_absolute_uri(reverse('organizations-member-invite', args=[organization.code]))
        message = f'Hello. You have been invited to the organization "{organization.name}" in Maestro. If you wish to accept the invitation, please head to {url} and click accept.'
        EmailMessage(mail_subject, message, to=[invitee_user.email]).send()

        messages.success(request, f"You have invited the user {invitee_user.get_full_name()} to the organization {organization.name}.")
        return HttpResponse()


@login_required
def organization_accept_invite(request, code):
    organization = get_object_or_404(Organization, code=code)
    user_membership = get_object_or_404(Membership, user=request.user, organization=organization)

    if user_membership.has_accepted is True:
        messages.error("You have already accepted the invite")
        return HttpResponseBadRequest()
    else:  # user_membership.has_accepted = False
        user_membership.has_accepted = True
        user_membership.join_date = now()
        user_membership.save()
        messages.success(request, f"You are now a member of the organization {organization.name}.")
        return HttpResponse()


# - If user is the only owner of the organization:
#   - If he is also the only user, then all the contexts of that organization are deleted
#   - If he is NOT the only user, and there not any more owners, then he has to make another user from the organization owner before leaving (if he wants to force and is the only user, he can also block/remove the other users from the organization, and then yes he can leave and delete)
@login_required
@user_is_member
def organization_leave(request, code):
    organization = get_object_or_404(Organization, code=code)
    user_membership = get_object_or_404(Membership, user=request.user, organization=organization)

    number_users_organization = Membership.objects.filter(organization=organization, is_blocked=False).count()  # only those who are not blocked count
    number_owners_organization = Membership.objects.filter(organization=organization, is_owner=True).count()  # owners can't be blocked, thus the extra condition doesn't is applied
    # user_membership.is_owner and number_owners_organization == 1 # user is the only owner
    if number_users_organization == 1:  # user is the only member of the organization
        # TODO: Delete all the contexts of the organization
        organization.delete()
        messages.success(request, 'You have left the organization successfully. Since you were the only owner, all the contexts have also been deleted.')
        return HttpResponse(status=200)
    elif user_membership.is_owner and number_owners_organization == 1:  # there is more than one (non-blocked) user in the organization, but there is only one owner => owner has to make another user owner before leaving
        messages.error(request, 'Since you are the only owner of the organization, another user must be made owner before leaving the organization.')
        return HttpResponseBadRequest()
    else:  # user is an owner of an organization where there are more owners, or is a regular user
        user_membership.delete()
        messages.success(request, 'You have left the organization successfully.')
        return HttpResponse(status=200)


@login_required
@user_is_owner
def block_user(request, code, user_email):
    action = request.GET.get('action', None)
    if not action or (action != 'block' and action != 'unblock'):
        return HttpResponseBadRequest()

    organization = get_object_or_404(Organization, code=code)
    user = get_object_or_404(User, email=unquote(user_email))
    current_user_membership = get_object_or_404(Membership, user=request.user, organization=organization)
    target_user_membership = get_object_or_404(Membership, user=user, organization=organization)

    if target_user_membership.is_owner:
        messages.error(request, 'Owners cannot be blocked')
        return HttpResponseForbidden()
    elif action == 'block' and target_user_membership.is_blocked:
        messages.error(request, 'The user already is blocked')
        return HttpResponseBadRequest()
    elif action == 'unblock' and not target_user_membership.is_blocked:
        messages.error(request, 'The user already is already unblocked')
        return HttpResponseBadRequest()
    else:  # Target user is member and current user is owner
        target_user_membership.is_blocked = True if action == 'block' else False
        target_user_membership.save()
        messages.success(request, f'{user.get_full_name()} is now {action}ed.')
        return HttpResponse(status=200)


@login_required
@user_is_owner
def make_user_owner(request, code, user_email):
    organization = get_object_or_404(Organization, code=code)
    user = get_object_or_404(User, email=unquote(user_email))
    current_user_membership = get_object_or_404(Membership, user=request.user, organization=organization)
    target_user_membership = get_object_or_404(Membership, user=user, organization=organization)

    if target_user_membership.is_owner:
        messages.error(request, 'Owners cannot be made owners again')
        return HttpResponseForbidden()
    else:  # Target user is member and current user is owner
        target_user_membership.is_owner = True
        target_user_membership.save()
        messages.success(request, f'You have set {user.get_full_name()} as an organization owner successfully.')
        return HttpResponse(status=200)



