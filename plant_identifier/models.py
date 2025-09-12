from django.db import models

class UserInfo(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)   # we’d normally hash this!
    

    def __str__(self):
        return self.username