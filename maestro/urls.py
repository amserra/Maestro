from django.contrib import admin
from django.urls import include, path

from django.conf import settings
from django.conf.urls import handler400, handler403, handler404, handler500
from django.conf.urls.static import static

urlpatterns = [
    path('', include('common.urls')),
    path('', include('account.urls')),
    path('organizations/', include('organization.urls')),
    path('contexts/', include('context.urls')),
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),
]

if not settings.DEBUG:
    handler400 = 'common.views.bad_request'
    handler403 = 'common.views.permission_denied'
    handler404 = 'common.views.page_not_found'
    handler500 = 'common.views.server_error'


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

