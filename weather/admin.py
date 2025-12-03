from django.contrib import admin

from .models import WeatherSample


@admin.register(WeatherSample)
class WeatherSampleAdmin(admin.ModelAdmin):
    """Admin interface for WeatherSample model."""
    list_display = ("city", "temperature_c", "windspeed_kmh", "observed_at", "created_at")
    list_filter = ("city", "observed_at")
    search_fields = ("city",)
    readonly_fields = ("created_at",)
