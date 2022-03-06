from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
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
from .models import SearchContext, Configuration
from .tasks import delete_context_folder, create_context_folder, gather_urls
from django.contrib import messages
from celery import chain


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
            resolved_url = resolve(self.from_url)
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
        configuration = form.save()
        if type(form).__name__ == EssentialConfigurationForm.__name__:
            self.context.configuration = configuration
            self.context.status = SearchContext.READY
            self.context.save()
        else:
            if self.context.configuration is None:
                context_conf = Configuration(advanced_configuration=configuration)
                context_conf.save()
                self.context.configuration = context_conf
                self.context.save()
            else:
                self.context.configuration.advanced_configuration = configuration
                self.context.save()
        return super().form_valid(form)


@login_required
@user_can_edit
def search_context_delete(request, code):
    context = get_object_or_404(SearchContext, code=code)

    if context.configuration:
        context.configuration.delete()
    context.delete()
    delete_context_folder.delay(context.owner_code, context.code)

    return redirect('contexts-list')


@login_required
@user_can_edit
def search_context_start(request, code):
    context = get_object_or_404(SearchContext, code=code)

    if not context.configuration:
        return HttpResponseBadRequest()

    context.status = SearchContext.GATHERING_URLS
    context.save()

    # chain(gather_urls.s())  # TODO: pass necessary data
    messages.success(request, 'Search context execution started successfully.')

    if request.META['HTTP_REFERER']:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return redirect('contexts-detail', code=context.code)
