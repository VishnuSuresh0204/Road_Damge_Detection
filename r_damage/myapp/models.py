from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class Login(AbstractUser):
    USER_TYPES = [
        ('Admin', 'Admin'),
        ('User', 'User'),
    ]

    usertype = models.CharField(
        max_length=50,
        choices=USER_TYPES,
        default='User'
    )
    viewpassword = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.username


class UserProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    profile_pic = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name

 