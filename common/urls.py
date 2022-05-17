from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('components/', views.ComponentsView.as_view(), name='components'),
    path('roadmap/', views.roadmap, name='roadmap'),
]