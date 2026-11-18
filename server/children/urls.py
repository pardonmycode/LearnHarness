from django.urls import path

from . import api

urlpatterns = [
    path("children/", api.children, name="children"),
    path("children/<str:profile_id>/", api.child_detail, name="child-detail"),
    path("children/<str:profile_id>/unlock/", api.child_unlock, name="child-unlock"),
    path("children/<str:profile_id>/progress/", api.child_progress, name="child-progress"),
]
