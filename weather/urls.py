from django.urls import path
from .views import fetch_weather, latest_weather

urlpatterns = [
    path("fetch/", fetch_weather, name="fetch_weather"),
    path("latest/", latest_weather, name="latest_weather"),
]
