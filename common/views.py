from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy

from common.models import SubmitPlugin
from django.views.generic import CreateView


def home(request):
    return render(request, 'common/home.html')


def roadmap(request):
    return render(request, 'common/roadmap.html')


def about(request):
    return render(request, 'common/about.html')


class ComponentsView(SuccessMessageMixin, CreateView):
    model = SubmitPlugin
    fields = ['submitter_name', 'submitter_email', 'plugin_name', 'kind', 'file']
    template_name = 'common/components.html'
    success_url = reverse_lazy('components')
    success_message = 'Plugin submitted. You will be contacted when the plugin is reviewed.'


# Error views
def bad_request(request, exception):
    context = {}
    return render(request, 'common/error.html', context, status=400)


def permission_denied(request, exception):
    context = {}
    return render(request, 'common/error.html', context, status=403)


def page_not_found(request, exception):
    context = {}
    return render(request, 'common/error.html', context, status=404)


def server_error(request):
    context = {}
    return render(request, 'common/error.html', context, status=500)
