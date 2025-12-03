"""
Celery configuration for the microfw project.

Sets up the Celery app with Django settings integration and automatic task discovery.
"""
from __future__ import annotations

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "microfw.settings")

app = Celery("microfw")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
