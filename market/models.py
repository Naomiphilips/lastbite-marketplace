# market/models.py

from django.db import models
from users.models import VendorProfile, CustomerProfile

class Bag(models.Model):
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    base_price_cents = models.PositiveIntegerField()
    current_price_cents = models.PositiveIntegerField()
    ready_after = models.DateTimeField()
    pickup_by = models.DateTimeField()
    status = models.CharField(max_length=20, default="listed")

    def __str__(self):
        return f"{self.title} ({self.vendor.business_name})"


class Order(models.Model):
    bag = models.ForeignKey(Bag, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    product = models.ForeignKey('business.Product', on_delete=models.CASCADE,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="reserved")

    # transaction tracking
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    total_cents = models.PositiveIntegerField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        item_name = self.product.title if self.product else (self.bag.title if self.bag else "Item")
        return f"Order #{self.id} - {item_name} - {self.customer.user.username}"

    class Meta:
        ordering = ['-created_at']
    
    def get_item(self):
        """Get the item (product or bag) for this order"""
        return self.product if self.product else self.bag
    
    def get_item_title(self):
        """Get the title of the item"""
        if self.product:
            return self.product.title
        elif self.bag:
            return self.bag.title
        return "Unknown Item"
    
    def get_total_dollars(self):
        """Get total in dollars"""
        if self.total_cents:
            return self.total_cents / 100
        return 0

class Cart(models.Model):
    """A shopping cart tied to an authenticated customer (CustomerProfile).
    """
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True)

    def total_cents(self):
        return sum(item.total_cents() for item in self.items.all())

    def __str__(self):
        return f"Cart({self.customer.user.username})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        'business.Product',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Keeping prev fields for backward compatability on migrations.
    bag = models.ForeignKey(Bag, on_delete=models.CASCADE, null=True, blank=True)
    listing_id = models.PositiveIntegerField(null=True, blank=True)
    listing_title = models.CharField(max_length=120, blank=True)
    unit_price_cents = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)

    def total_cents(self):
        return self.unit_price_cents * self.quantity

    def __str__(self):
        if self.product:
            return f"{self.product.title} x{self.quantity}"

        name = self.listing_title if self.listing_title else (self.bag.title if self.bag else "Item")
        return f"{name} x{self.quantity}"
