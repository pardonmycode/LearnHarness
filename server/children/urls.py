from django.urls import path

from . import api, device_api

urlpatterns = [
    path("children/", api.children, name="children"),
    path("children/<str:profile_id>/", api.child_detail, name="child-detail"),
    path("children/<str:profile_id>/unlock/", api.child_unlock, name="child-unlock"),
    path("children/<str:profile_id>/progress/", api.child_progress, name="child-progress"),
    path("children/<str:profile_id>/missions/", api.child_missions, name="child-missions"),
    path(
        "children/<str:profile_id>/missions/<str:mission_id>/done/",
        api.child_mission_done,
        name="child-mission-done",
    ),
    path("devices/requests/", device_api.create_request, name="device-requests"),
    path(
        "devices/requests/<str:request_id>/",
        device_api.request_status,
        name="device-request-status",
    ),
    path("missions/", api.missions, name="missions"),
    path("missions/<str:mission_id>/", api.mission_detail, name="mission-detail"),
]
