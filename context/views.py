from __future__ import annotations

import os
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import resolve
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, FormView
from django.views.generic.edit import ModelFormMixin
from django_filters.views import FilterView
from common.decorators import PaginatedFilterView
from common.mixins import SafePaginationMixin
from .authorization import UserHasAccess, UserCanEdit, user_can_edit
from .filters import SearchContextFilter
from .forms import SearchContextCreateForm, AdvancedConfigurationForm, EssentialConfigurationForm
from .helpers import get_user_search_contexts
from .models import SearchContext, Configuration, AdvancedConfiguration, Filter
from .tasks import delete_context_folder, create_context_folder, fetch_urls, run_default_gatherer, run_post_processors, run_filters, run_classifiers
from django.contrib import messages
from celery import chain
from django.conf import settings
import json


class SearchContextListView(LoginRequiredMixin, SafePaginationMixin, PaginatedFilterView, FilterView):
    template_name = 'context/list.html'
    context_object_name = 'contexts'
    paginate_by = 4
    filterset_class = SearchContextFilter

    def get_queryset(self):
        contexts = get_user_search_contexts(self.request.user)
        return contexts.order_by('status')


class SearchContextCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = 'context/create.html'
    model = SearchContext
    form_class = SearchContextCreateForm
    success_message = 'The search context was created successfully.'

    def get_success_url(self):
        # Conditionally choose success url based on the name of the button clicked
        if 'create_configure' in self.request.POST:
            return reverse_lazy('contexts-configuration-update', args=[self.object.code])
        else:
            return reverse_lazy('contexts-detail', args=[self.object.code])

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
        context.status = SearchContext.NOT_CONFIGURED
        context.save()
        create_context_folder.delay(context.owner_code, context.code)
        return super().form_valid(form)


class SearchContextDetailView(LoginRequiredMixin, UserHasAccess, DetailView):
    template_name = 'context/detail.html'
    model = SearchContext
    slug_field = 'code'
    slug_url_kwarg = 'code'
    context_object_name = 'context'


class SearchContextConfigurationDetailView(LoginRequiredMixin, UserHasAccess, DetailView):
    model = Configuration
    context_object_name = 'configuration'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context = get_object_or_404(SearchContext, code=self.kwargs.get('code'))
        self.page = self.request.GET.get('page', None)

    def get_template_names(self):
        if self.page == 'advanced':
            return ['context/configuration_detail_advanced.html']
        else:
            return ['context/configuration_detail_essential.html']

    def get_object(self, queryset=None):
        if self.page == 'advanced':
            return self.context.configuration.advanced_configuration
        else:
            return self.context.configuration

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['context'] = self.context
        return context


class SearchContextConfigurationCreateOrUpdateView(LoginRequiredMixin, UserCanEdit, SuccessMessageMixin, ModelFormMixin, FormView):
    http_method_names = ['get', 'post']
    template_name = 'context/configuration_configure.html'
    success_message = 'The search context was configured successfully.'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context = get_object_or_404(SearchContext, code=self.kwargs.get('code'))
        self.from_url = self.request.GET.get('from', None)
        self.form = self.request.GET.get('form', None)

        if self.form == 'advanced' and self.context.configuration and self.context.configuration.advanced_configuration:
            self.object = self.context.configuration.advanced_configuration
        elif (self.form == 'essential' or self.form is None) and self.context.configuration:
            self.object = self.context.configuration
        else:
            self.object = None

    def get_success_url(self):
        if self.from_url:
            resolved_url = resolve(self.from_url.split('?', 1)[0])  # resolve only works if no query params are in the url
            if self.form:
                return f"{reverse_lazy(resolved_url.url_name, args=[resolved_url.kwargs['code']])}?page={self.form}"
            else:
                return reverse_lazy(resolved_url.url_name, args=[resolved_url.kwargs['code']])
        else:
            return reverse_lazy('contexts-detail', args=[self.context.code])

    def get_form(self, form_class=None):
        if self.form and self.form == 'advanced':
            form_class = AdvancedConfigurationForm
        else:
            form_class = EssentialConfigurationForm

        return form_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['context'] = self.context
        return context

    def form_valid(self, form):
        configuration: Configuration | AdvancedConfiguration = form.save()

        if type(form).__name__ == EssentialConfigurationForm.__name__:
            essential_configuration: Configuration = configuration
            self.context.configuration = essential_configuration
            self.context.status = SearchContext.READY
            self.context.save()
        else:
            advanced_configuration: AdvancedConfiguration = configuration
            # Save coordinates
            if form.cleaned_data['location']:
                lat, long, radius = form.cleaned_data['location'].split(',')
                advanced_configuration.location = f'{lat},{long}'
                advanced_configuration.radius = float(radius)
                advanced_configuration.save()

            if self.context.configuration is None:
                advanced_configuration.save()
                context_conf = Configuration(advanced_configuration=advanced_configuration)
                context_conf.save()
                self.context.configuration = context_conf
                self.context.save()
            else:
                self.context.configuration.advanced_configuration = advanced_configuration
                self.context.configuration.save()
        return super().form_valid(form)


@login_required
@user_can_edit
def search_context_delete(request, code):
    context = get_object_or_404(SearchContext, code=code)
    delete_context_folder.delay(context.id)

    messages.success(request, 'Context deleted successfully.')
    return redirect('contexts-list')


@login_required
@user_can_edit
def search_context_start(request, code):
    context = get_object_or_404(SearchContext, code=code)

    if not context.configuration:
        return HttpResponseBadRequest()

    if context.status != SearchContext.READY:
        return HttpResponseBadRequest()

    chain(fetch_urls.s(context.id), run_default_gatherer.s(context.id)).apply_async()
    messages.success(request, 'Search context execution started successfully.')

    if request.META['HTTP_REFERER']:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return redirect('contexts-detail', code=context.code)


class SearchContextStatusView(LoginRequiredMixin, UserHasAccess, DetailView):
    template_name = 'context/status.html'
    model = SearchContext
    slug_field = 'code'
    slug_url_kwarg = 'code'
    context_object_name = 'context'

    def get(self, request, *args, **kwargs):
        context_status = self.get_object().status

        # Requested status by javascript
        if 'status' in request.GET:
            return JsonResponse({'status': context_status})

        forbidden_states = [SearchContext.NOT_CONFIGURED, SearchContext.READY]
        if context_status in forbidden_states:
            return redirect('contexts-detail', code=self.get_object().code)

        # Normal get request for template
        return super().get(request, *args, **kwargs)


class SearchContextDataReviewView(LoginRequiredMixin, UserHasAccess, DetailView):
    model = SearchContext
    slug_field = 'code'
    slug_url_kwarg = 'code'
    context_object_name = 'context'

    def get_template_names(self):
        search_context = self.get_object()
        if search_context.configuration.data_type == Configuration.IMAGES:
            return ['context/review_images.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_context: SearchContext = self.get_object()
        if search_context.configuration.data_type == Configuration.IMAGES:
            # Media folder where the thumbs are
            folder = os.path.join(settings.MEDIA_ROOT, search_context.owner_code, search_context.code)
            files = os.listdir(folder)

            # Pagination
            paginator = Paginator(files, 15)
            page_number = self.request.GET.get('page', None)
            if page_number is not None:
                page_obj = paginator.get_page(page_number)
            else:
                page_obj = paginator.get_page(1)

            context['page_obj'] = page_obj
            context['files'] = page_obj.object_list
        return context


@login_required
@user_can_edit
def save_images_review(request, code):
    if not request.method == 'POST':
        return HttpResponseBadRequest()

    context = get_object_or_404(SearchContext, code=code)

    if context.status != SearchContext.WAITING_DATA_REVISION:
        return HttpResponseBadRequest()

    files = request.POST.get('files', None)
    if files is None:
        return HttpResponseBadRequest()

    files = files.split(',')

    media_folder = context.context_folder_media
    thumb_folder = os.path.join(context.context_folder, 'data', 'thumbs')
    original_folder = os.path.join(context.context_folder, 'data', 'full')
    for file in files:
        os.remove(os.path.join(media_folder, file))
        os.remove(os.path.join(thumb_folder, file))
        os.remove(os.path.join(original_folder, file))

    messages.success(request, 'Alterations made successfully.')
    return redirect('contexts-review', code=context.code)


@login_required
@user_can_edit
def complete_review(request, code):
    """Complete review and continue process"""
    context = get_object_or_404(SearchContext, code=code)

    if context.status != SearchContext.WAITING_DATA_REVISION:
        return HttpResponseBadRequest()

    chain(run_post_processors.s(context.id), run_filters.s(context.id), run_classifiers.s(context.id)).apply_async()
    messages.success(request, 'Process underway.')
    return redirect('contexts-detail', code=context.code)
