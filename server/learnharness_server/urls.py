from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "LearnHarness – Verwaltung"
admin.site.site_title = "LearnHarness"
admin.site.index_title = "Kinder, Gruppen und Zugänge"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("children.urls")),
]
