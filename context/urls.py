from django.urls import path

from . import views

urlpatterns = [
    path('', views.SearchContextListView.as_view(), name='contexts-list'),
    path('new/', views.SearchContextCreateView.as_view(), name='contexts-new'),
    path('<str:code>/', views.SearchContextDetailView.as_view(), name='contexts-detail'),
    path('<str:code>/configuration/', views.SearchContextConfigurationDetailView.as_view(), name='contexts-configuration-detail'),
    path('<str:code>/configuration/update/', views.SearchContextConfigurationCreateView.as_view(), name='contexts-configuration-update'),
    path('<str:code>/delete/', views.search_context_delete, name='contexts-delete'),
    path('<str:code>/start/', views.search_context_start, name='contexts-start'),
]
