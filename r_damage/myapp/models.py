from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class Login(AbstractUser):

    usertype = models.CharField(
        max_length=50,
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

 
class RoadDamage(models.Model):
 
    DAMAGE_TYPES = [
        ('Pothole', 'Pothole'),
        ('Crack', 'Crack'),
        ('Surface Damage', 'Surface Damage'),
        ('Broken Road', 'Broken Road'),
        ('No Damage', 'No Damage'),
    ]
 
    SEVERITY = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
 
    STATUS = [
        ('Reported', 'Reported'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
        ('Assigned', 'Assigned'),
        ('Under Repair', 'Under Repair'),
        ('Completed', 'Completed'),
    ]
 
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='road_damages'
    )
 
    image = models.ImageField(upload_to='road_damage/')
 
    # Image with YOLO bounding boxes drawn on it (generated after detection)
    result_image = models.ImageField(
        upload_to='road_damage/results/',
        null=True,
        blank=True
    )
 
    damage_type = models.CharField(
        max_length=50,
        choices=DAMAGE_TYPES,
        blank=True
    )
 
    confidence = models.FloatField(null=True, blank=True)
 
    # Fraction of the image area covered by the detected damage (0-100)
    damage_area_percent = models.FloatField(null=True, blank=True)
 
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY,
        blank=True
    )
 
    description = models.TextField(blank=True)
 
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, blank=True)
 
    reported_date = models.DateTimeField(auto_now_add=True)
 
    status = models.CharField(
        max_length=30,
        choices=STATUS,
        default='Reported'
    )
 
    class Meta:
        ordering = ['-reported_date']
 
    def __str__(self):
        return f"{self.damage_type or 'Pending'} - {self.severity or 'N/A'}"
 