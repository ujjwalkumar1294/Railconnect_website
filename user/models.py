from django.db import models

# Create your models here.


class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    otp = models.CharField(max_length=6, blank=True, null=True)
    

    def __str__(self):
        return self.username