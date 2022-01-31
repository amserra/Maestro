from django.urls import path

from . import views

urlpatterns = [
    path('', views.OrganizationListView.as_view(), name='organizations-list'),
    path('new/', views.OrganizationCreateView.as_view(), name='organizations-new'),
    path('leave/', views.organization_leave, name='organizations-leave'),
]