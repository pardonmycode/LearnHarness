"""Settings for the local test stand: SQLite file, no device token, only on this computer.

Started by ``python -m learnharness_client.teststand``; never meant for a school server.
"""

import os

os.environ.setdefault("DJANGO_DEBUG", "1")

from .settings import *  # noqa: E402,F403
from .settings import BASE_DIR, MIDDLEWARE, STORAGES  # noqa: E402

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
# Only reachable from this computer, so the app needs no device token.
TUTOR_REQUIRE_TOKEN = False
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("TESTSTAND_DB", str(BASE_DIR / "teststand.sqlite3")),
    }
}
# The development server serves static files itself; no collectstatic needed.
MIDDLEWARE = [item for item in MIDDLEWARE if not item.startswith("whitenoise.")]
STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
