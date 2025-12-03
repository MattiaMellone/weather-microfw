"""
Test settings for running tests with SQLite instead of PostgreSQL.
"""
from .settings import *  # noqa: F403, F401

# Use SQLite for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use a simple password hasher for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable Celery during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
