from django.db import models
from django.contrib.auth.models import User

class SavedPlant(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_plants',
        null=True,
        blank=True,
    )
    species_id = models.IntegerField()  # Not globally unique
    common_name = models.CharField(max_length=200)
    scientific_name = models.CharField(max_length=200)
    confidence = models.FloatField(null=True, blank=True)
    image_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'species_id'], name='unique_species_per_user')
        ]

    def __str__(self):
        username = self.user.username if self.user else "No User"
        return f"{self.common_name} ({username})"



class PlantHistory(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='plant_history',
        null=True,
        blank=True,
    )
    species_id = models.IntegerField()
    common_name = models.CharField(max_length=200)
    scientific_name = models.CharField(max_length=200)
    confidence = models.FloatField(null=True, blank=True)
    image_url = models.URLField(blank=True, null=True)
    identified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'species_id'], name='unique_history_per_user')
        ]
        ordering = ['-identified_at']

    def __str__(self):
        username = self.user.username if self.user else "No User"
        return f"{self.common_name} ({username}) - {self.identified_at.strftime('%Y-%m-%d %H:%M')}"