from django.db import models

# Create your models here.
class Staff(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # Store hashed
    role = models.CharField(max_length=20, default='admin')

    def __str__(self):
        return self.username