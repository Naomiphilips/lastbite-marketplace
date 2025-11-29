# File location: business/models.py 

from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError
from market.models import Cart, CartItem
from users.models import CustomerProfile
import logging

class Listing(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings"
    )
    title = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    image = models.FileField(upload_to="listings/", blank=True, null=True)  

    # Dynamic pricing fields
    min_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Minimum bid price for barter bids")
    end_time = models.DateTimeField(null=True, blank=True, help_text="End time for dynamic pricing.")
    
    # Location fields
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_current_price(self):
        """
        Calculate the current price based on dynamic pricing rules.
        Returns the base price if dynamic pricing is not configured.
        
        Discount tiers:
        - Less than 30 minutes remaining: 20% discount
        - Less than 1 hour (but >= 30 min): 15% discount
        - More than 1 hour: 10% discount
        
        Price never goes below min_price if set.
        """
        # If dynamic pricing is not configured, return base price
        
        if not self.end_time:
            return self.price
        
        now = timezone.now()
        
        # If end_time has passed, return regular price

        if now >= self.end_time:
            return self.price
        
        # Calculate time remaining

        time_remaining = self.end_time - now
        total_seconds = time_remaining.total_seconds()
        minutes_remaining = total_seconds / 60

        # Determine discount percentage

        if minutes_remaining < 30:
            discount_percent = Decimal('0.20')  # 20% discount
        elif minutes_remaining < 60:
            discount_percent = Decimal('0.15')  # 15% discount
        else:
            discount_percent = Decimal('0.10')  # 10% discount
        
        # Calculate discounted price
        discounted_price = self.price * (Decimal('1') - discount_percent)

        return discounted_price
    
    @property
    def current_price(self):
        """Property accessor for get_current_price()"""
        return self.get_current_price()
    
    class Meta:
        ordering = ['-created_at']

class Product(models.Model):
    """
    Creating unifiied product model for items as we had listings here and bags in the market.
    Both used different pricing details and dynamic pricing rules causing confusion and unecessary complexity.
    """

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products"
    )

    # Base info
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    image = models.FileField(upload_to="products/", blank=True, null=True)
    notes = models.TextField(blank=True, help_text="Internal notes about the product.")

    # Pricing - Using decimal
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The initial price when the product becomes available"
    )

    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum price for dynamic pricing. Floor price for bids."
    )

    # Inventory
    quantity = models.PositiveIntegerField(default=1)

    # Status
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("listed", "Listed"),
        ("reserved", "Reserved"),
        ("sold", "Sold"),
        ("expired", "Expired"),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default="draft"
    )

    # Time-based discount
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="End time for dynamic discounts"
    )
    
    # Bidding toggle
    enable_bidding = models.BooleanField(
        default=False,
        help_text="Enable bidding/bartering for this product"
    )

    # Add after enable_bidding field
    winning_bid = models.OneToOneField(
        'Bid',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='winning_product',
        help_text="The winning bid for this product (set when bidding ends)"
    )

    # Location
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.owner.username})"

    def get_current_price(self):
        """
        Current price based on pricing_type and time.
        Returns base price if dynamic price is not configured.
        """

        if not self.end_time:
            return self.base_price

        now = timezone.now()

       
        if now >= self.end_time:
            return self.base_price

        time_remaining = self.end_time - now
        minutes_remaining = time_remaining.total_seconds() / 60

        # Discount tiers - 20% , 15%, 10%
        if minutes_remaining < 30:
            discount_percent = Decimal('0.20')
        elif minutes_remaining < 60:
            discount_percent = Decimal('0.15')
        else:
            discount_percent = Decimal('0.10') 
        
        discounted_price = self.base_price * (Decimal('1') - discount_percent)

        # Never go below min_price
        if self.min_price:
            return max(discounted_price, self.min_price)
        return discounted_price

    @property
    def current_price(self):
        return self.get_current_price()

    def refresh_dynamic_price(self, save=False):
        """
        Recalculate and update current_price.
        """
        return self.get_current_price()
    
    def is_available(self):
        """
        Check if product is available for sale.
        """
        if self.status != "listed":
            return False
        if self.quantity <= 0:
            return False
        return True
    
    def get_highest_bid(self):
        """Get the highest bid for this product"""
        return self.bids.first()  # Since bids are ordered by -amount
    
    def get_highest_bid_amount(self):
        """Get the highest bid amount, or None if no bids"""
        highest = self.get_highest_bid()
        return highest.amount if highest else None
    
    def is_bidding_open(self):
        """Check if bidding is currently open for this product"""
        if not self.enable_bidding:
            return False  # Bidding must be explicitly enabled
        if not self.min_price or not self.end_time:
            return False  # Bidding requires both min_price and end_time
        if not self.is_available():
            return False
        
        # Auto-process expiration if end_time has passed
        now = timezone.now()
        if now >= self.end_time:
            # Process expiration automatically
            self.process_expiration_if_needed()
            return False
        
        return True
    
    def get_minimum_bid(self):
        """Get the minimum bid amount (highest bid + increment, or min_price)"""
        highest = self.get_highest_bid_amount()
        if highest:
            # Minimum bid is highest bid + $0.50 increment
            return highest + Decimal('0.50')
        return self.min_price if self.min_price else self.base_price

    def process_expiration_if_needed(self):
        """
        Automatically process expiration and select winner if end_time has passed.
        This is called automatically when checking bidding status or viewing products.
        Returns True if processing occurred, False otherwise.
        """
        # Only process if bidding was enabled and end_time has passed
        if not self.enable_bidding:
            return False
        
        if not self.end_time:
            return False
        
        now = timezone.now()
        if now < self.end_time:
            # Not expired yet
            return False
        
        # Already processed if status is not 'listed' or winning_bid is set
        if self.status != 'listed' or self.winning_bid:
            return False
        
        # Process expiration
        highest_bid = self.get_highest_bid()
        
        if highest_bid:
            # Select winner
            self.winning_bid = highest_bid
            self.status = 'reserved'
            self.save(update_fields=['winning_bid', 'status'])
        
            try:
                # Get the winning bidder's customer profile
                customer_profile = CustomerProfile.objects.get(user=highest_bid.bidder)
                
                # Get or create their cart
                cart, created = Cart.objects.get_or_create(customer=customer_profile)
                
                # Check if item is already in cart
                existing_item = CartItem.objects.filter(
                    cart=cart,
                    product=self
                ).first()
                
                if existing_item:
                    # Update quantity if already exists
                    existing_item.quantity = 1  # or however you want to handle quantity
                    existing_item.unit_price_cents = int(highest_bid.amount * 100)
                    existing_item.save()
                else:
                    # Add new item to cart
                    CartItem.objects.create(
                        cart=cart,
                        product=self,
                        unit_price_cents=int(highest_bid.amount * 100),
                        quantity=1
                    )
            except Exception as e:
                # Log error but don't fail the expiration process
                
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to add winning bid to cart: {e}")
            
            return True

        else:
            # No bids, mark as expired
            self.status = 'expired'
            self.save(update_fields=['status'])
            return False

    def get_winning_bidder(self):
        """Get the winning bidder, if one exists"""
        # Process expiration first if needed
        self.process_expiration_if_needed()
        if self.winning_bid:
            return self.winning_bid.bidder
        return None

    def has_winner(self):
        """Check if this product has a winning bid"""
        self.process_expiration_if_needed()
        return self.winning_bid is not None


class Bid(models.Model):
    """
    Bid model for barter/auction functionality.
    Needs min price and end time to bet set.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="bids"
    )
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bids"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Bid amount"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-amount', '-created_at']  # Highest bid first, then most recent
        indexes = [
            models.Index(fields=['product', '-amount']),
            models.Index(fields=['bidder']),
        ]
    
    def __str__(self):
        return f"${self.amount} on {self.product.title} by {self.bidder.username}"
    
    def clean(self):
        """Validate bid amount"""
        from django.core.exceptions import ValidationError
        
        # Check if product is set
        if not self.product:
            return  # Skip validation if product not set (will be set by form)
        
        if self.product.min_price and self.amount < self.product.min_price:
            raise ValidationError(f"Bid must be at least ${self.product.min_price}")
        
        # Check if bidding is still open
        if self.product.end_time and timezone.now() >= self.product.end_time:
            raise ValidationError("Bidding has ended for this product")
        
        # Check if product is available
        if not self.product.is_available():
            raise ValidationError("This product is no longer available for bidding")