from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('components/', views.components, name='components'),
    path('roadmap/', views.roadmap, name='roadmap'),
]