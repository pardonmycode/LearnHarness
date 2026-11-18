from django.contrib import admin
from django.urls import include, path

from children import views
from tutor import urls as tutor_urls

admin.site.site_header = "LearnHarness – Verwaltung"
admin.site.site_title = "LearnHarness"
admin.site.index_title = "Kinder, Gruppen und Zugänge"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("children.urls")),
    path("api/v1/", include(tutor_urls.urlpatterns)),
    path("ki/", include(tutor_urls.staff_urlpatterns)),
    path("uebersicht/", views.overview, name="overview"),
    path("uebersicht/<str:selection>/", views.overview, name="overview-group"),
    path("uebersicht/<str:selection>/export.csv", views.overview_csv, name="overview-csv"),
    path("uebersicht/kind/<str:profile_id>/", views.child_history, name="child-history"),
    path(
        "uebersicht/kind/<str:profile_id>/verlauf.csv",
        views.child_history_csv,
        name="child-history-csv",
    ),
]
