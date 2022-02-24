from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from common.mixins import SafePaginationMixin, TitleMixin
from .forms import SearchContextCreateForm
from .models import SearchContext


class DashboardView(LoginRequiredMixin, SafePaginationMixin, ListView):
    template_name = 'context/dashboard.html'
    context_object_name = 'contexts'
    paginate_by = 4

    def get_queryset(self):
        contexts_user = SearchContext.objects.filter(user=self.request.user)
        contexts_user_organizations = SearchContext.objects.filter(
            organization__membership__user=self.request.user,
            organization__membership__is_blocked=False,
            organization__membership__has_accepted=True
        )
        return contexts_user | contexts_user_organizations


class SearchContextCreateView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, CreateView):
    title = 'Create a search context'
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
