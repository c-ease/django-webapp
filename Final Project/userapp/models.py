from django.db import models
from django.conf import settings

# Create your models here.

class stock_picks(models.Model):
    name = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    symbols = models.TextField()

