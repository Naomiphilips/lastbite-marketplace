# market/forms.py
from django import forms
from .models import Bag

class BagForm(forms.ModelForm):
    base_price = forms.DecimalField(
        label="Starting Price ($)",
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01",
            "min": "0"
        }),
        help_text="The initial price when the bag becomes available"
    )
    min_price = forms.DecimalField(
        label="Minimum Price ($)",
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01",
            "min": "0"
        }),
        help_text="The lowest price the bag will reach (must be less than starting price)"
    )
    
    class Meta:
        model = Bag
        fields = ["title", "description", "ready_after", "pickup_by"]
        exclude = ["vendor", "current_price_cents", "status", "created_at"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "ready_after": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control"
            }),
            "pickup_by": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control"
            }),
        }
        labels = {
            "ready_after": "Ready After",
            "pickup_by": "Pickup By (End Time)",
        }
    
    def __init__(self, *args, vendor_profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        if vendor_profile:
            self.instance.vendor = vendor_profile
        
        # If editing existing bag, populate form fields with dollar values
        if self.instance and self.instance.pk:
            if self.instance.base_price_cents:
                self.fields["base_price"].initial = self.instance.base_price_cents / 100
            if self.instance.min_price_cents:
                self.fields["min_price"].initial = self.instance.min_price_cents / 100
    
    def clean(self):
        cleaned_data = super().clean()
        base_price = cleaned_data.get("base_price")
        min_price = cleaned_data.get("min_price")
        ready_after = cleaned_data.get("ready_after")
        pickup_by = cleaned_data.get("pickup_by")
        
        # Validate min_price is less than base_price
        if base_price and min_price and min_price >= base_price:
            raise forms.ValidationError("Minimum price must be less than starting price.")
        
        # Validate min_price is not negative
        if min_price and min_price < 0:
            raise forms.ValidationError("Minimum price cannot be negative.")
        
        # Validate dates
        if ready_after and pickup_by and ready_after >= pickup_by:
            raise forms.ValidationError("Pickup by (end time) must be after ready after time.")
        
        # Convert dollars to cents
        if base_price is not None:
            cleaned_data["base_price_cents"] = int(base_price * 100)
        if min_price is not None:
            cleaned_data["min_price_cents"] = int(min_price * 100)
        
        return cleaned_data
    
    def save(self, commit=True):
        bag = super().save(commit=False)
        # The cents values were set in clean() and stored in cleaned_data
        # We need to set them on the instance
        if 'base_price_cents' in self.cleaned_data:
            bag.base_price_cents = self.cleaned_data['base_price_cents']
        if 'min_price_cents' in self.cleaned_data:
            bag.min_price_cents = self.cleaned_data['min_price_cents']
        if commit:
            bag.save()
        return bag