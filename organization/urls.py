from django.urls import path

from . import views

urlpatterns = [
    path('', views.OrganizationListView.as_view(), name='organizations-list'),
    path('new/', views.OrganizationCreateView.as_view(), name='organizations-new'),
    path('leave/', views.organization_leave, name='organizations-leave'),
    path('settings/<str:code>/', views.OrganizationSettingsView.as_view(), name='organizations-settings'),
    path('<str:code>/', views.OrganizationDetailView.as_view(), name='organizations-detail'),
    path('<str:code>/members/', views.OrganizationMembersView.as_view(), name='organizations-member-list'),
    path('<str:code>/members/<str:user_email>/make-owner', views.make_user_owner, name='organizations-member-make-owner'),
]
