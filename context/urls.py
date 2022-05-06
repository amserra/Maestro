from django.urls import path

from . import views

urlpatterns = [
    path('', views.SearchContextListView.as_view(), name='contexts-list'),
    path('new/', views.SearchContextCreateView.as_view(), name='contexts-new'),
    path('<str:code>/', views.SearchContextDetailView.as_view(), name='contexts-detail'),
    path('<str:code>/configuration/', views.SearchContextConfigurationDetailView.as_view(), name='contexts-configuration-detail'),
    path('<str:code>/configuration/update/', views.SearchContextConfigurationCreateOrUpdateView.as_view(), name='contexts-configuration-update'),
    path('<str:code>/delete/', views.search_context_delete, name='contexts-delete'),
    path('<str:code>/start/', views.search_context_start, name='contexts-start'),
    path('<str:code>/status/', views.SearchContextStatusView.as_view(), name='contexts-status'),
    path('<str:code>/status/task/<str:task>/', views.PipelineProcessDetail.as_view(), name='task-status'),
    path('<str:code>/review/', views.SearchContextDataReviewView.as_view(), name='contexts-review'),
    path('<str:code>/review/save/', views.save_images_review, name='contexts-review-save'),
    path('<str:code>/review/complete/', views.complete_review, name='contexts-review-complete'),
    path('<str:code>/results/', views.SearchContextDataReviewView.as_view(), name='contexts-results'),
    path('<str:code>/results/<str:objectId>', views.SearchContextDataObjectReviewView.as_view(), name='contexts-results-object'),
    path('<str:code>/download-results/', views.download_results, name='contexts-download-results'),
    path('<str:code>/rerun/', views.rerun_from_stage, name='contexts-rerun'),
]
