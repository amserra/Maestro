from django.shortcuts import render


def home(request):
    return render(request, 'common/home.html')


def roadmap(request):
    return render(request, 'common/roadmap.html')


def about(request):
    return render(request, 'common/about.html')
