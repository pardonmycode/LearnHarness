from django.contrib import admin
from django.urls import include, path

from children import views

admin.site.site_header = "LearnHarness – Verwaltung"
admin.site.site_title = "LearnHarness"
admin.site.index_title = "Kinder, Gruppen und Zugänge"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("children.urls")),
    path("uebersicht/", views.overview, name="overview"),
    path("uebersicht/<str:selection>/", views.overview, name="overview-group"),
]
