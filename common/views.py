from django.shortcuts import render


def home(request):
    return render(request, 'common/home.html')


def roadmap(request):
    return render(request, 'common/roadmap.html')


def about(request):
    return render(request, 'common/about.html')


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
