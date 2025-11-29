# users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from .models_businessreg import BusinessRegistration 

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        VENDOR   = "vendor", "Vendor"
        ADMIN    = "admin", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)

    def is_vendor(self):   return self.role == self.Role.VENDOR
    def is_customer(self): return self.role == self.Role.CUSTOMER


class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendor_profile")
    business_name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    approved = models.BooleanField(default=False)
    def __str__(self): return self.business_name


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")
    phone = models.CharField(max_length=30, blank=True)
    def __str__(self): return self.user.username


from .models_businessreg import *   
