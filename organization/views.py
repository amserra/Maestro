from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.utils import timezone as tz
from django.contrib import messages
from common.mixins import SafePaginationMixin, TitleMixin
from .authorization import UserIsOwner
from .forms import OrganizationCreateForm, OrganizationSettingsForm
from .models import Organization, Membership


class OrganizationListView(LoginRequiredMixin, SafePaginationMixin, ListView):
    template_name = 'organization/list.html'
    context_object_name = 'organizations'
    paginate_by = 5

    def get_queryset(self):
        return self.request.user.organization_set.all().order_by('id')

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


class OrganizationSettingsView(LoginRequiredMixin, UserIsOwner, TitleMixin, SuccessMessageMixin, UpdateView):
    title = 'Update organization %s settings'
    template_name = 'organization/form.html'
    success_url = reverse_lazy('organizations-list')
    model = Organization
    form_class = OrganizationSettingsForm
    slug_field = 'code'
    slug_url_kwarg = 'code'
    success_message = 'Your have updated the organization\'s settings'


# - If user is the only owner of the organization:
#   - If he is also the only user, then all the contexts of that organization are deleted
#   - If he is NOT the only user, and there not any more owners, then he has to make another user from the organization owner before leaving (if he wants to force and is the only user, he can also block/remove the other users from the organization, and then yes he can leave and delete)
@login_required
def organization_leave(request):
    organization_code = request.GET.get('organization', '')
    user_membership = Membership.objects.filter(user=request.user, organization__code=organization_code)
    if user_membership.exists():
        user_membership = user_membership.first()
        number_users_organization = Membership.objects.filter(organization__code=organization_code, is_blocked=False).count()  # only those who are not blocked count
        number_owners_organization = Membership.objects.filter(organization__code=organization_code, is_owner=True).count()  # owners can't be blocked, thus the extra condition doesn't is applied
        # user_membership.is_owner and number_owners_organization == 1 # user is the only owner
        if number_users_organization == 1:  # user is the only member of the organization
            # TODO: Delete all the contexts of the organization
            Organization.objects.get(code=organization_code).delete()
            messages.success(request, 'You have left the organization successfully. Since you were the only owner, all the contexts have also been deleted.')
            return HttpResponse(status=200)
        elif user_membership.is_owner and number_owners_organization == 1:  # there is more than one (non-blocked) user in the organization, but there is only one owner => owner has to make another user owner before leaving
            messages.error(request, 'Since you are the only owner of the organization, another user must be made owner before leaving the organization.')
            return HttpResponse(status=400)
        else:  # user is an owner of an organization where there are more owners, or is a regular user
            user_membership.delete()
            messages.success(request, 'You have left the organization successfully.')
            return HttpResponse(status=200)
    else:  # this should not happen. A user should only be able to do this request on an organization he is member of
        return HttpResponse(status=400)
