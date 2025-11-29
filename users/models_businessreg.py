# users/models_businessreg.py

from django.db import models
from django.conf import settings   

#business reg form
class BusinessRegistration(models.Model):
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business",
        null=True,
        blank=True,
    )
#types of business choices. Added in more options!
    BUSINESS_TYPE_CHOICES = [
        ("bakery", "Bakery"),
        ("cafe", "Cafe"),
        ("grocery", "Grocery / Market"),
        ("caterer", "Caterer"),
        ("food_truck", "Food Truck"),
        ("restaurant", "Restaurant"),
        ("other", "Other"),
    ]

    #adding in limits based on the proper length/format needed.

    name = models.CharField(max_length=120)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    owner_name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    logo = models.FileField(
        upload_to="business_logos/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.name} ({self.email})"
