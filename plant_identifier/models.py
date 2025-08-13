from django.db import models

class SavedPlant(models.Model):
    common_name = models.CharField(max_length=255)
    scientific_name = models.CharField(max_length=255)
    image_url = models.URLField()

    def __str__(self):
        return self.common_name
