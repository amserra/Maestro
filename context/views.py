from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from common.mixins import SafePaginationMixin, TitleMixin
from organization.authorization import UserIsMember
from .authorization import UserHasAccess
from .forms import SearchContextCreateForm
from .helpers import get_user_search_contexts
from .models import SearchContext


class DashboardView(LoginRequiredMixin, SafePaginationMixin, ListView):
    template_name = 'context/list.html'
    context_object_name = 'contexts'
    paginate_by = 4

    def get_queryset(self):
        contexts = get_user_search_contexts(self.request.user)
        return contexts.order_by('status')


class SearchContextCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = 'context/create.html'
    success_url = reverse_lazy('contexts-list')
    model = SearchContext
    form_class = SearchContextCreateForm
    success_message = 'The search context was created successfully.'

    def get_form_kwargs(self):
        kwargs = super(SearchContextCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        context = form.save(commit=False)
        owner = form.cleaned_data['owner']
        if '@' in owner:
            owner_object = self.request.user
        else:
            owner_object = self.request.user.organizations_active.get(code=owner)

        context.owner = owner_object
        context.code = form.cleaned_data['name'].replace(' ', '-').lower()
        context.save()
        return super().form_valid(form)


class SearchContextDetailView(LoginRequiredMixin, UserHasAccess, DetailView):
    template_name = 'context/detail.html'
    model = SearchContext
    slug_field = 'code'
    slug_url_kwarg = 'code'
    context_object_name = 'context'
