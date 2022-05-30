from __future__ import annotations
import io
import os
from zipfile import ZipFile
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, FormView
from django.views.generic.edit import ModelFormMixin
from django_filters.views import FilterView
from common.decorators import PaginatedFilterView
from common.mixins import SafePaginationMixin
from .authorization import UserHasAccess, UserCanEdit, user_can_edit, user_has_access
from .filters import SearchContextFilter
from .forms import SearchContextCreateForm, EssentialConfigurationForm, FetchingAndGatheringConfigurationForm, PostProcessingConfigurationForm, FilteringConfigurationForm, ClassificationConfigurationForm, ProvidingConfigurationForm
from .helpers import get_user_search_contexts, compare_status, compare_status_leq
from .models import SearchContext, Configuration, AdvancedConfiguration
from .tasks import delete_context_folder, create_context_folder, run_fetchers, run_default_gatherer, run_post_processors, run_filters, run_classifiers, run_provider, handle_initial_datastream
from django.contrib import messages
from celery import chain
import json
import ast
from .tasks.helpers import read_log
from .tasks.provide import generate_json


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
        context.creator = self.request.user
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

        if self.context.status == SearchContext.FINISHED_PROVIDING:
            context['canStop'] = True if self.context.configuration.repeat_amount and not self.context.is_stopped else False
        else:
            unstoppable_states = [
                SearchContext.NOT_CONFIGURED,
                SearchContext.READY,
                SearchContext.FAILED_FETCHING_URLS,
                SearchContext.FAILED_GATHERING_DATA,
                SearchContext.WAITING_DATA_REVISION,
                SearchContext.FAILED_POST_PROCESSING,
                SearchContext.FAILED_FILTERING,
                SearchContext.FAILED_CLASSIFYING,
                SearchContext.FAILED_PROVIDING
            ]
            context['canStop'] = False if self.context.status in unstoppable_states or self.context.is_stopped else True

        return context


class SearchContextConfigurationCreateOrUpdateView(LoginRequiredMixin, UserCanEdit, SuccessMessageMixin, ModelFormMixin, FormView):
    http_method_names = ['get', 'post']
    template_name = 'context/configuration_configure.html'
    success_message = 'The search context was updated successfully.'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context = get_object_or_404(SearchContext, code=self.kwargs.get('code'))
        self.from_url = self.request.GET.get('from', None)
        self.form = self.request.GET.get('form', 'essential')  # default is essential

        if (self.form == 'advanced' or self.form == 'fetch' or self.form == 'post-process' or self.form == 'filter' or self.form == 'classify' or self.form == 'provide') and self.context.configuration and self.context.configuration.advanced_configuration:
            self.object = self.context.configuration.advanced_configuration
        elif self.form == 'essential' and self.context.configuration:
            self.object = self.context.configuration
        else:
            self.object = None

    def get_success_url(self):
        # Button "update and continue"
        if 'update_continue' in self.request.POST:
            return f"{reverse_lazy('contexts-configuration-update', args=[self.context.code])}?form={self.form}"

        if self.from_url and self.form:
            if self.form == 'essential':
                return reverse_lazy('contexts-configuration-detail', args=[self.context.code])
            else:
                return f"{reverse_lazy('contexts-configuration-detail', args=[self.context.code])}?page=advanced"
        else:
            return reverse_lazy('contexts-detail', args=[self.context.code])

    def get_form(self, form_class=None):
        if self.form and (self.form == 'fetch' or self.form == 'advanced'):
            form_class = FetchingAndGatheringConfigurationForm
        elif self.form and self.form == 'post-process':
            form_class = PostProcessingConfigurationForm
        elif self.form and self.form == 'filter':
            form_class = FilteringConfigurationForm
        elif self.form and self.form == 'classify':
            form_class = ClassificationConfigurationForm
        elif self.form and self.form == 'provide':
            form_class = ProvidingConfigurationForm
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
            if self.object is None:
                self.context.status = SearchContext.READY
            self.context.save()
        else:
            advanced_configuration: AdvancedConfiguration = configuration

            # Save coordinates
            if type(form).__name__ == FilteringConfigurationForm.__name__:
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

            # Unzip file
            if type(form).__name__ == FetchingAndGatheringConfigurationForm.__name__:
                initial_datastream = self.context.configuration.advanced_configuration.initial_datastream
                current_initial_datastream = None if initial_datastream is None or initial_datastream == '' else initial_datastream
                new_initial_datastream = form.cleaned_data['initial_datastream']

                if form.cleaned_data['initial_datastream'] and current_initial_datastream != new_initial_datastream:
                    handle_initial_datastream.delay(self.context.id, self.context.configuration.advanced_configuration.initial_datastream.path)
                elif form.cleaned_data['initial_datastream'] is None and current_initial_datastream is not None:
                    # TODO: handle remove
                    pass

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

    context.is_stopped = False
    context.save()
    chain(run_fetchers.s(context.id), run_default_gatherer.s(context.id), run_post_processors.s(context.id), run_filters.s(context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
    messages.success(request, 'Search context execution started successfully.')

    if request.META['HTTP_REFERER']:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return redirect('contexts-detail', code=context.code)


class SearchContextStatusView(LoginRequiredMixin, UserHasAccess, DetailView):
    """View requested used both to render the context/status.html page, and to respond to status requests"""
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

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context = get_object_or_404(SearchContext, code=self.kwargs.get('code'))
        self.view_type = self.request.GET.get('type', 'grid')
        allowed_status = compare_status(self.context.status, SearchContext.WAITING_DATA_REVISION)
        if not allowed_status or self.context.number_of_iterations == 0:
            return redirect(to='/')

    def get_template_names(self):
        search_context = self.get_object()
        if search_context.configuration.data_type == Configuration.IMAGES:
            return ['context/results_grid_image.html'] if self.view_type == 'grid' else ['context/results_list_image.html']
        elif search_context.configuration.data_type == Configuration.SOUNDS:
            return ['context/results_list_sound.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_context: SearchContext = self.get_object()
        if search_context.configuration.data_type == Configuration.IMAGES or search_context.configuration.data_type == Configuration.SOUNDS:
            objects = search_context.datastream.all()

            # Pagination
            paginator = Paginator(objects, 15)
            page_number = self.request.GET.get('page', None)
            if page_number is not None:
                page_obj = paginator.get_page(page_number)
            else:
                page_obj = paginator.get_page(1)

            context['page_obj'] = page_obj
            context['objects'] = page_obj.object_list
            context['title'] = 'Gathered data' if self.context.status == SearchContext.WAITING_DATA_REVISION else 'Results'
            context['view_type'] = self.view_type
        return context


@login_required
@user_can_edit
def save_data_review(request, code):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    context = get_object_or_404(SearchContext, code=code)

    if context.status != SearchContext.WAITING_DATA_REVISION:
        return HttpResponseBadRequest()

    files = request.POST.get('files', None)
    if files is None:
        return HttpResponseBadRequest()

    files = files.split(',')

    if context.configuration.data_type == Configuration.IMAGES:
        static_folder = context.context_folder_static
        thumb_folder = os.path.join(context.context_folder, 'data', 'thumbs')
        original_folder = os.path.join(context.context_folder, 'data', 'full')
        for file in files:
            original_folder_file_path = os.path.join(original_folder, file)
            thumb_folder_file_path = os.path.join(thumb_folder, file)
            static_folder_file_path = os.path.join(static_folder, file)

            db_object = context.datastream.filter(data=original_folder_file_path)
            if db_object.exists() and db_object.count() == 1:
                db_object = db_object[0]
                try:
                    os.remove(original_folder_file_path)
                    os.remove(thumb_folder_file_path)
                    os.remove(static_folder_file_path)
                    db_object.delete()
                except Exception as ex:
                    print(ex)
                    messages.error(request, 'Something went wrong while saving. Please try again later.')

    elif context.configuration.data_type == Configuration.SOUNDS:
        static_folder = context.context_folder_static
        original_folder = os.path.join(context.context_folder, 'data')
        for file in files:
            original_folder_file_path = os.path.join(original_folder, file)
            static_folder_file_path = os.path.join(static_folder, file)

            db_object = context.datastream.filter(data=original_folder_file_path)
            if db_object.exists() and db_object.count() == 1:
                db_object = db_object[0]
                try:
                    os.remove(original_folder_file_path)
                    os.remove(static_folder_file_path)
                    db_object.delete()
                except Exception as ex:
                    print(ex)
                    messages.error(request, 'Something went wrong while saving. Please try again later.')

    messages.success(request, 'Alterations made successfully.')
    return redirect('contexts-results', code=context.code)


@login_required
@user_can_edit
def complete_review(request, code):
    """Complete review and continue process"""
    context = get_object_or_404(SearchContext, code=code)

    if context.status != SearchContext.WAITING_DATA_REVISION:
        return HttpResponseBadRequest()

    context.is_stopped = False
    context.save()
    chain(run_post_processors.s(True, context.id), run_filters.s(context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
    messages.success(request, 'Process underway.')
    return redirect('contexts-detail', code=context.code)


class PipelineProcessDetail(LoginRequiredMixin, UserHasAccess, DetailView):
    template_name = 'context/task_info.html'
    model = SearchContext
    slug_field = 'code'
    slug_url_kwarg = 'code'
    context_object_name = 'context'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task'] = self.kwargs['task']
        lines = read_log(self.get_object(), self.kwargs['task'])
        context['content'] = lines
        return context


@login_required
@user_has_access
def download_results(request, code):
    context = get_object_or_404(SearchContext, code=code)

    if context.status != SearchContext.FINISHED_PROVIDING and context.number_of_iterations == 0:
        return HttpResponseBadRequest()

    if not context.configuration.advanced_configuration or not context.configuration.advanced_configuration.classifiers:
        return HttpResponseBadRequest()

    classifiers = context.configuration.advanced_configuration.classifiers.filter(is_active=True)

    json_data = generate_json(classifiers, context.datastream, context.configuration.advanced_configuration.keep_null)
    json_obj = json.dumps(json_data, indent=4)

    return HttpResponse(json_obj, headers={
        'Content-Type': 'application/json',
        'Content-Disposition': 'attachment; filename="results.json"'
    })


@login_required
@user_has_access
def download_files(request, code):
    context = get_object_or_404(SearchContext, code=code)

    if context.status != SearchContext.FINISHED_PROVIDING and context.number_of_iterations == 0:
        return HttpResponseBadRequest()

    if not context.configuration.advanced_configuration or not context.configuration.advanced_configuration.classifiers:
        return HttpResponseBadRequest()

    filtered_datastream = context.datastream.filter(filtered=False)
    files = [obj.data for obj in filtered_datastream]

    zip_buffer = io.BytesIO()
    with ZipFile(zip_buffer, 'w') as zip_file:
        for file in files:
            zip_file.write(filename=file, arcname=os.path.basename(file))

    return HttpResponse(zip_buffer.getvalue(), headers={
        'Content-Type': 'application/zip',
        'Content-Disposition': 'attachment; filename=files.zip'
    })


@login_required
@user_can_edit
def rerun_from_stage(request, code):
    context = get_object_or_404(SearchContext, code=code)
    current_status = context.status

    stage = request.GET.get('stage', None)

    if stage is None or current_status == SearchContext.NOT_CONFIGURED or current_status == SearchContext.READY:
        return HttpResponseBadRequest()

    # had like this: and compare_status_leq(SearchContext.FINISHED_FETCHING_URLS, current_status)
    if stage == 'fetch':
        chain(run_fetchers.s(context.id), run_default_gatherer.s(context.id), run_post_processors.s(context.id), run_filters.s(context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
    elif stage == 'gather':
        try:
            with open(f'{context.context_folder}/urls.txt', 'r') as f:
                urls_list_str = f.read()
            urls_list = ast.literal_eval(urls_list_str)
            chain(run_default_gatherer.s(urls_list, context.id), run_post_processors.s(context.id), run_filters.s(context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
        except:
            chain(run_default_gatherer.s([], context.id), run_post_processors.s(context.id), run_filters.s(context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
    elif stage == 'post-process':
        chain(run_post_processors.s(True, context.id), run_filters.s(context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
    elif stage == 'filter':
        chain(run_filters.s(True, context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
    elif stage == 'classify':
        chain(run_classifiers.s(True, context.id), run_provider.s(context.id)).apply_async()
    elif stage == 'provide':
        run_provider.delay(True, context.id)
    else:
        return HttpResponseBadRequest()

    context.is_stopped = False
    context.save()
    messages.success(request, f'Starting execution from {stage} stage.')
    return HttpResponse(status=200)


class SearchContextDataObjectReviewView(LoginRequiredMixin, UserHasAccess, DetailView):
    model = SearchContext
    slug_field = 'code'
    slug_url_kwarg = 'code'
    context_object_name = 'context'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context = get_object_or_404(SearchContext, code=self.kwargs.get('code', None))
        self.obj = [el for el in self.context.datastream.all() if el.identifier == self.kwargs.get('objectId', None)]
        if not self.obj or len(self.obj) == 0 or self.context.number_of_iterations == 0:
            raise Http404

        self.obj = self.obj[0]

        allowed_status = compare_status(self.context.status, SearchContext.FINISHED_PROVIDING)
        if not allowed_status:
            raise Http404

    def get_template_names(self):
        search_context = self.get_object()
        if search_context.configuration.data_type == Configuration.IMAGES:
            return ['context/object_detail_image.html']
        elif search_context.configuration.data_type == Configuration.SOUNDS:
            return ['context/object_detail_sound.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['context'] = self.context
        context['obj'] = self.obj
        return context


@login_required
@user_can_edit
def stop_execution(request, code):
    context = get_object_or_404(SearchContext, code=code)
    context.is_stopped = True
    context.save()

    messages.info(request, 'The execution has been stopped')
    return redirect('contexts-detail', code=context.code)


@login_required
@user_can_edit
def resume_execution(request, code):
    context = get_object_or_404(SearchContext, code=code)
    context.is_stopped = False
    context.save()

    status = context.status
    if SearchContext.FETCHING_URLS in status:
        chain(run_fetchers.s(context.id), run_default_gatherer.s(context.id), run_post_processors.s(context.id), run_filters.s(context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
    elif SearchContext.GATHERING_DATA in status:
        try:
            with open(f'{context.context_folder}/urls.txt', 'r') as f:
                urls_list_str = f.read()
            urls_list = ast.literal_eval(urls_list_str)
            chain(run_default_gatherer.s(urls_list, context.id), run_post_processors.s(context.id), run_filters.s(context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
        except:
            chain(run_default_gatherer.s([], context.id), run_post_processors.s(context.id), run_filters.s(context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
    elif SearchContext.POST_PROCESSING in status:
        chain(run_post_processors.s(True, context.id), run_filters.s(context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
    elif SearchContext.FILTERING in status:
        chain(run_filters.s(True, context.id), run_classifiers.s(context.id), run_provider.s(context.id)).apply_async()
    elif SearchContext.CLASSIFYING in status:
        chain(run_classifiers.s(True, context.id), run_provider.s(context.id)).apply_async()
    elif SearchContext.PROVIDING in status:
        run_provider.delay(True, context.id)

    messages.success(request, 'The execution has been resumed')
    return redirect('contexts-detail', code=context.code)
