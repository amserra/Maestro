from django.urls import path

from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='contexts-list'),
    path('new/', views.SearchContextCreateView.as_view(), name='contexts-new'),
    path('<str:code>/', views.SearchContextDetailView.as_view(), name='contexts-detail'),
]
