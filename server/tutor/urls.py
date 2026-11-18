from django.urls import path

from . import api, views
from .consumers import TutorStreamConsumer

# Mounted under /api/v1/ next to the administration API (paths as the app expects them).
urlpatterns = [
    path("health", api.health, name="tutor-health"),
    path("sessions", api.sessions, name="tutor-sessions"),
    path("sessions/<str:session_id>/hints", api.hints, name="tutor-hints"),
    path("tasks/<str:task_id>", api.task_detail, name="tutor-task"),
    path("tasks/<str:task_id>/submissions", api.code_submission, name="tutor-code-submission"),
    path(
        "exercises/<str:exercise_id>/submissions",
        api.exercise_submission,
        name="tutor-exercise-submission",
    ),
    path("progress", api.progress, name="tutor-progress"),
]

websocket_urlpatterns = [
    path("api/v1/sessions/<str:session_id>/stream", TutorStreamConsumer.as_asgi()),
]

staff_urlpatterns = [
    path("prompts/", views.prompt_overview, name="tutor-prompts"),
    path("verbindung-testen/", views.test_connection, name="tutor-test-connection"),
]
