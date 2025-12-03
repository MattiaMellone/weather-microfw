from django.db import models


class WeatherSample(models.Model):
    city = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    temperature_c = models.FloatField()
    windspeed_kmh = models.FloatField()
    observed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-observed_at"]
