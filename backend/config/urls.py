from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "EcoVision — администрирование"
admin.site.site_title = "EcoVision"
admin.site.index_title = "Управление справочником и распознаваниями"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("accounts.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("recognition.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
