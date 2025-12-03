"""
Data models for storing weather observations.
"""
from django.db import models


class WeatherSample(models.Model):
    """
    Represents a single weather observation for a specific location and time.
    
    Stores temperature, wind speed, and coordinates along with temporal metadata
    for both the observation time and record creation time.
    """
    city = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    temperature_c = models.FloatField()
    windspeed_kmh = models.FloatField()
    observed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-observed_at"]
        
    def __str__(self) -> str:
        """Return a human-readable representation of the weather sample."""
        return f"{self.city} @ {self.observed_at}: {self.temperature_c}°C"
