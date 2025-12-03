from django.urls import path
from .views import enqueue_weather_fetch, latest_weather

urlpatterns = [
    path("fetch/", enqueue_weather_fetch, name="enqueue_weather_fetch"),
    path("latest/", latest_weather, name="latest_weather"),
]
