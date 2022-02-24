from django.urls import path

from . import views

urlpatterns = [
    path('', views.OrganizationListView.as_view(), name='organizations-list'),
    path('invites/', views.OrganizationInvitesView.as_view(), name='organizations-invites'),
    path('new/', views.OrganizationCreateView.as_view(), name='organizations-new'),
    path('<str:code>/', views.OrganizationDetailView.as_view(), name='organizations-detail'),
    path('<str:code>/leave/', views.organization_leave, name='organizations-leave'),
    path('<str:code>/settings/', views.OrganizationSettingsView.as_view(), name='organizations-settings'),
    path('<str:code>/members/', views.OrganizationMembersView.as_view(), name='organizations-member-list'),
    path('<str:code>/members/invite', views.organization_invite_member, name='organizations-member-invite'),
    path('<str:code>/members/accept_invite', views.organization_accept_invite, name='organizations-member-accept_invite'),
    path('<str:code>/members/decline_invite', views.organization_decline_invite, name='organizations-member-decline_invite'),
    path('<str:code>/members/<str:user_email>/', views.OrganizationUserProfileView.as_view(), name='organizations-member-profile'),
    path('<str:code>/members/<str:user_email>/make-owner', views.make_user_owner, name='organizations-member-make-owner'),
    path('<str:code>/members/<str:user_email>/block', views.block_user, name='organizations-member-block'),
]
