"""
Main package initialization for the microfw project.

Imports the Celery app to ensure it's loaded when Django starts,
enabling automatic task discovery and scheduled jobs.
"""
from __future__ import annotations

from .celery import app as celery_app

__all__ = ("celery_app",)
