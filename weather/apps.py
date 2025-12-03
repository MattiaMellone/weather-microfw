"""
Django application configuration for the weather app.
"""
from django.apps import AppConfig


class WeatherConfig(AppConfig):
    """Configuration class for the weather application."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "weather"
