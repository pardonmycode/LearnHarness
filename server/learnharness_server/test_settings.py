"""Settings for pytest: SQLite unless POSTGRES_DB is set (CI runs against PostgreSQL)."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key")

from .settings import *  # noqa: E402,F403
from .settings import MIDDLEWARE, STORAGES  # noqa: E402

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
# Tests do not run collectstatic, so serve static files the plain Django way.
MIDDLEWARE = [item for item in MIDDLEWARE if not item.startswith("whitenoise.")]
STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
