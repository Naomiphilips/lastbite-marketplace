from django import forms
from django.utils import timezone
from .models import Listing, Product, Bid
from decimal import Decimal

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ["title", "price", "quantity", "notes", "image", "min_price", "end_time"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "min_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # The datetime will be stored in UTC format in a data attribute
        if self.instance and self.instance.pk and self.instance.end_time:


            # Store UTC ISO string in data attribute
            utc_iso = self.instance.end_time.isoformat()
            self.fields['end_time'].widget.attrs['data-utc-time'] = utc_iso

    def clean_end_time(self):
        """Use UTC datetime from hidden field if provided, otherwise convert naive datetime"""
        # Check if UTC time was submitted via hidden field

        end_time_utc = self.data.get('end_time_utc')
        if end_time_utc:

            # Parse the UTC ISO string
            from datetime import datetime
            try:

                # Handle both 'Z' and '+00:00' formats
                if end_time_utc.endswith('Z'):
                    end_time_str = end_time_utc.replace('Z', '+00:00')
                else:

                    end_time_str = end_time_utc
                
                end_time = datetime.fromisoformat(end_time_str)

                # Make it timezone-aware if needed

                if timezone.is_naive(end_time):
                    end_time = timezone.make_aware(end_time, timezone.utc)
                
                return end_time
            except Exception as e:
                pass
        
        # Fallback to regular field processing

        
        end_time = self.cleaned_data.get('end_time')
        
        if end_time:

            if timezone.is_naive(end_time):
                # Interpret as UTC

                end_time = timezone.make_aware(end_time, timezone.utc)
        return end_time

class ProductForm(forms.ModelForm):
    enable_bidding = forms.BooleanField(
        required=False,
        label="Enable Bidding/Bartering",
        help_text="Allow customers to place bids on this product"
    )
    
    class Meta:
        model = Product
        fields = ["title", "description", "base_price", "min_price", "quantity", "image", 
                  "end_time", "enable_bidding"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "min_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "base_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "enable_bidding": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set status to "listed" by default for new products
        if not self.instance.pk:
            self.instance.status = "listed"
        
        # Set initial value for enable_bidding based on existing instance
        if self.instance.pk:
            # Bidding is enabled if min_price and end_time are set
            self.fields['enable_bidding'].initial = bool(self.instance.min_price and self.instance.end_time)
        
        # Handle datetime fields
        if self.instance and self.instance.pk and self.instance.end_time:
            utc_iso = self.instance.end_time.isoformat()
            self.fields['end_time'].widget.attrs['data-utc-time'] = utc_iso
        
        # Add IDs for JavaScript
        self.fields['enable_bidding'].widget.attrs['id'] = 'id_enable_bidding'
        self.fields['min_price'].widget.attrs['id'] = 'id_min_price'
        self.fields['end_time'].widget.attrs['id'] = 'id_end_time'

    def clean(self):
        cleaned_data = super().clean()
        base_price = cleaned_data.get('base_price')
        min_price = cleaned_data.get('min_price')
        enable_bidding = cleaned_data.get('enable_bidding')
        end_time = cleaned_data.get('end_time')
        
        # If bidding is enabled, require min_price and end_time
        if enable_bidding:
            if not min_price:
                raise forms.ValidationError("Minimum price is required when bidding is enabled.")
            if not end_time:
                raise forms.ValidationError("End time is required when bidding is enabled.")
            if min_price >= base_price:
                raise forms.ValidationError("Minimum price must be less than base price when bidding is enabled.")
        else:
            # If bidding is disabled, clear min_price if it was set
            if min_price:
                cleaned_data['min_price'] = None
        
        # Validate min_price < base_price (only if min_price is set)
        if base_price and min_price and min_price >= base_price:
            raise forms.ValidationError("Minimum price must be less than base price.")
        
        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        
        # If bidding is disabled, clear min_price
        if not self.cleaned_data.get('enable_bidding'):
            product.min_price = None
        
        if commit:
            product.save()
        return product

    def clean_end_time(self):
        end_time_utc = self.data.get('end_time_utc')
        if end_time_utc:
            from datetime import datetime
            try:
                if end_time_utc.endswith('Z'):
                    end_time_str = end_time_utc.replace('Z', '+00:00')
                else:
                    end_time_str = end_time_utc
                
                end_time = datetime.fromisoformat(end_time_str)
                if timezone.is_naive(end_time):
                    end_time = timezone.make_aware(end_time, timezone.utc)
                return end_time
            except Exception as e:
                pass
        
        end_time = self.cleaned_data.get('end_time')
        if end_time:
            if timezone.is_naive(end_time):
                end_time = timezone.make_aware(end_time, timezone.utc)
        return end_time

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'class': 'form-control',
                'placeholder': 'Enter bid amount'
            })
        }

    def __init__(self, *args, product=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        self.user = user
        
        # Set product and user on instance for model validation
        if product:
            self.instance.product = product
        if user:
            self.instance.bidder = user
        
        if product:
            min_bid = product.get_minimum_bid()
            self.fields['amount'].widget.attrs['min'] = str(min_bid)
            self.fields['amount'].help_text = f"Minimum bid: ${min_bid:.2f}"
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if not self.product:
            raise forms.ValidationError("Product is required")
        
        if not self.product.is_bidding_open():
            raise forms.ValidationError("Bidding is not open for this product")
        
        min_bid = self.product.get_minimum_bid()
        if amount < min_bid:
            raise forms.ValidationError(
                f"Bid must be at least ${min_bid:.2f}. "
                f"{'Current highest bid' if self.product.get_highest_bid() else 'Minimum price'}: ${min_bid:.2f}"
            )
        
        # Check if user is the product owner
        if self.user and self.user == self.product.owner:
            raise forms.ValidationError("You cannot bid on your own product")
        
        return amount
    
    def clean(self):
        """Set product on instance before validation"""
        cleaned_data = super().clean()
        
        # Set product and bidder on instance so model.clean() can access them
        if self.product:
            self.instance.product = self.product
        if self.user:
            self.instance.bidder = self.user
        
        return cleaned_data

    def save(self, commit=True):
        bid = super().save(commit=False)
        if self.product:
            bid.product = self.product
        if self.user:
            bid.bidder = self.user
        if commit:
            bid.save()
        return bid
