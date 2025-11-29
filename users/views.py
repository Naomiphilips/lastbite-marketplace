# users/views.py
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth import login
from django.shortcuts import render
from datetime import datetime
from users.models import CustomerProfile
from market.models import Order
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from market.models import Order  # 👈 import your real Order
from users.models import CustomerProfile  # to map request.user -> customer profile

from .forms import RegistrationForm


class RegisterView(FormView): 
    template_name = 'register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('dashboard') 

    def form_valid(self, form):
        user = form.save()           
        login(self.request, user)
        return super().form_valid(form)


@login_required
def user_history(request):
    """
    Shows the current user's orders.
    Right now this will be empty until checkout actually creates Order rows.
    TODO (checkout team): make sure you create Order objects with the correct status.
    """
    orders = []


    try:
        customer_profile = CustomerProfile.objects.get(user=request.user)

        orders = (
            Order.objects
            .filter(customer=customer_profile)
            .select_related("bag", "bag__vendor", "product", "product__owner")
            .order_by("-created_at")
        )

    
        for o in orders:
            if o.product:
                # Product order
                o.item_title = o.product.title
                o.item_price_dollars = o.get_total_dollars() / o.quantity if o.quantity > 0 else 0
                o.total_dollars = o.get_total_dollars()
                o.vendor_name = o.product.owner.username
                o.subtype = "Item"
                o.detail_url = f"/business/products/{o.product.pk}/public/"
            elif o.bag:
                # Bag order (legacy)
                o.item_title = o.bag.title
                o.item_price_dollars = o.bag.current_price_cents / 100 if o.bag.current_price_cents else 0
                o.total_dollars = o.bag.current_price_cents / 100 if o.bag.current_price_cents else 0
                o.vendor_name = o.bag.vendor.business_name if o.bag.vendor else "Unknown"
                o.subtype = "Item"
                o.detail_url = "#"
            else:
                o.item_title = "Unknown Item"
                o.item_price_dollars = 0
                o.total_dollars = 0
                o.vendor_name = "Unknown"
                o.subtype = "Item"
                o.detail_url = "#"

    except CustomerProfile.DoesNotExist:
        # user has no customer profile yet -> no orders, just show empty state
        orders = []

    context = {
        "items": orders,
    }
    return render(request, "users/history.html", context)