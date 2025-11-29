# market/views
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from django.contrib import messages
from .models import Bag, Cart, CartItem, Order
from business.models import Product, Listing
from users.models import CustomerProfile
from django.db import transaction


# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def _get_or_create_cart(user):
    # Auto-create CustomerProfile if it doesn't exist (for users with customer role)
    customer = getattr(user, 'customer_profile', None)
    if customer is None:
        # Only create CustomerProfile if user is a customer
        if user.role == user.Role.CUSTOMER or user.is_customer():
            from users.models import CustomerProfile
            customer, _ = CustomerProfile.objects.get_or_create(user=user)
        else:
            return None
    
    cart, _ = Cart.objects.get_or_create(customer=customer)
    return cart


@login_required
def cart_detail(request):
    cart = _get_or_create_cart(request.user)
    if cart:
        items = cart.items.select_related('product','bag').all()
        for item in items:
            if item.product:
                # Check if product has a winning bid (user won the auction)
                if item.product.winning_bid and item.product.winning_bid.bidder == request.user:
                    # Use the winning bid amount instead of current price
                    winning_price = float(item.product.winning_bid.amount)
                    item.unit_price = winning_price
                    item.unit_price_cents = int(winning_price * 100)
                else:
                    # Use current price for regular products
                    current_price = item.product.get_current_price()
                    item.unit_price = float(current_price)
                    item.unit_price_cents = int(current_price * 100)
                item.save(update_fields=['unit_price_cents'])
            else:
                item.unit_price = item.unit_price_cents / 100

            item.total_price = item.unit_price * item.quantity
        total = sum(item.total_price for item in items)
    else:
        items = []
        total = 0

    return render(request, 'market/cart_detail.html', {'cart': cart, 'items': items, 'total': total})


@require_POST
@login_required
def add_to_cart(request):
    cart = _get_or_create_cart(request.user)
    if cart is None:
        return redirect('users:login')

    product_id = request.POST.get('product_id')
    bag_id = request.POST.get('bag_id')
    listing_id = request.POST.get('listing_id')
    quantity = int(request.POST.get('quantity', 1))

    if product_id:
        product = get_object_or_404(Product, pk=product_id)

        # Check if available
        if not product.is_available():
            messages.error(request, "This product is no longer available.")
            return redirect(request.META.get('HTTP_REFERER', "market:dynamic_pricing"))

        # Check quantity availability
        requested_quantity = int(request.POST.get('quantity', 1))
        if requested_quantity > product.quantity:
            messages.error(request, f"Only {product.quantity} item(s) available. You requested {requested_quantity}.")
            return redirect(request.META.get('HTTP_REFERER', "market:dynamic_pricing"))

        current_price = product.get_current_price()
        unit_price_cents = int(current_price * 100)

        

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'unit_price_cents': unit_price_cents,
                'quantity': quantity
            }
        )
        if not created:
            total_cart_quantity = item.quantity + quantity
            if total_cart_quantity > product.quantity:
                messages.error(request, f"Only {product.quantity} item(s) available. You already have {item.quantity} in cart.")
                return redirect(request.META.get('HTTP_REFERER', "market:dynamic_pricing"))
            item.unit_price_cents = unit_price_cents
            item.quantity += quantity
            item.save()

    # Legacy support for bags to ensure compatibility 
    elif bag_id:
        bag = get_object_or_404(Bag, pk=bag_id)
        unit_price = bag.current_price_cents
        item, _ = CartItem.objects.get_or_create(cart=cart, bag=bag, defaults={'unit_price_cents': unit_price, 'quantity': quantity})
        if not _:
            item.quantity += quantity
            item.save()

    # Legacy support for listings to ensure compatibility
    elif listing_id:
        listing = get_object_or_404(Listing, pk=listing_id)

        if hasattr(listing, 'get_current_price'):
            current_price = listing.get_current_price()
        else:
            current_price = listing.price
        unit_price = int(listing.price * 100)
        item, created = CartItem.objects.get_or_create(cart=cart, listing_id=listing.id, defaults={'listing_title': listing.title, 'unit_price_cents': unit_price, 'quantity': quantity})
        if not created:
            item.unit_price_cents = unit_price
            item.quantity += quantity
            item.save()

    # Redirect back to the referring page, or cart if 'next' parameter is provided
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)

    return redirect('market:cart_detail')


@require_POST
@login_required
def update_cart_item(request, item_id):
    cart = _get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', item.quantity))
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save()
    return redirect('market:cart_detail')


@require_POST
@login_required
def remove_cart_item(request, item_id):
    cart = _get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    return redirect('market:cart_detail')

@login_required
def dynamic_pricing(request):
    """
    View for dynamic pricing/barter page for products with time_based pricing.
    """
    products = Product.objects.filter(
        status="listed",
        quantity__gt=0,
    ).select_related("owner")

    return render(request, "market/bag_list.html", {"bags": products, "products": products})
    bags = Bag.objects.filter(status="listed").select_related("vendor")
    # Recalculate prices on access
    for bag in bags:
        bag.refresh_dynamic_price(save=True)
    return render(request, "market/bag_list.html", {"bags": bags})

# Fix the function name (typo: strip_config -> stripe_config)
@login_required
def stripe_config(request):  # Fixed typo
    """Return Stripe publishable key"""
    return JsonResponse({
        'publishableKey': settings.STRIPE_PUBLISHABLE_KEY,
    })

@require_POST
@login_required
def create_checkout_session(request):
    """Create Stripe Checkout Session"""
    cart = _get_or_create_cart(request.user)
    if not cart or not cart.items.exists():
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    items = cart.items.select_related('bag', 'product').all()
    
    # Build line items for Stripe
    line_items = []
    for item in items:
        if item.product:
            # Handle Bag items
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.title,
                        'description': item.product.description[:500] if item.product.description else '',
                    },
                    'unit_amount': item.unit_price_cents,
                },
                'quantity': item.quantity,
            })

        elif item.bag:
            # Handle Bag items
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.bag.title,
                        'description': item.bag.description[:500] if item.bag.description else '',
                    },
                    'unit_amount': item.unit_price_cents,
                },
                'quantity': item.quantity,
            })
        elif item.listing_title:
            # Handle Listing items (legacy)
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.listing_title,
                    },
                    'unit_amount': item.unit_price_cents,
                },
                'quantity': item.quantity,
            })

    if not line_items:
        return JsonResponse({'error': 'No valid items in cart'}, status=400)

    try:
        domain_url = request.build_absolute_uri('/')[:-1]  # Remove trailing slash
        


        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=domain_url + '/market/checkout/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + '/market/checkout/cancelled/',
            client_reference_id=str(request.user.id) if request.user.is_authenticated else None,
            customer_email=request.user.email if request.user.email else None,
        )
        
        return JsonResponse({'sessionId': checkout_session['id']})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


class SuccessView(TemplateView):
    """Success page after payment"""
    template_name = 'market/checkout_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = self.request.GET.get('session_id')
        
        if session_id:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                context['session'] = session
                
                # Process order if payment successful
                if session.payment_status == 'paid':
                    existing_orders = Order.objects.filter(stripe_session_id=session_id)
                    if existing_orders.exists():
                        cart = _get_or_create_cart(self.request.user)
                        if cart:
                            CartItem.objects.filter(cart=cart).delete()
                        messages.info(self.request, "Order already processed.")
                    else:
                        # Process new order
                        cart = _get_or_create_cart(self.request.user)
                        if cart:
                            try:
                                with transaction.atomic():
                                    # Create orders for each item
                                    customer = cart.customer
                                    # Get items list before clearing to avoid queryset issues
                                    cart_items = list(cart.items.select_related('bag', 'product').all())
                                    
                                    for item in cart_items:
                                        if item.product:
                                            # Decrease product quantity
                                            product = item.product
                                            order_quantity = item.quantity
                                            
                                            # Ensure don't oversell
                                            if order_quantity > product.quantity:
                                                messages.error(self.request, f"Not enough stock for {product.title}. Available: {product.quantity}, Requested: {order_quantity}")
                                                continue
                                            
                                            # Decrease quantity
                                            product.quantity -= order_quantity
                                            
                                            # Update status based on remaining quantity
                                            if product.quantity <= 0:
                                                product.status = 'sold'
                                            # If quantity > 0, keep status as 'listed' (don't change to 'reserved')
                                            
                                            product.save(update_fields=['quantity', 'status'])

                                            # Create Order for Product
                                            Order.objects.create(
                                                product=item.product,
                                                customer=customer,
                                                status='reserved',
                                                stripe_session_id=session_id,
                                                payment_intent_id=session.payment_intent,
                                                total_cents=item.total_cents(),
                                                quantity=item.quantity
                                            )
                                        
                                        
                                        elif item.bag:
                                            # Create Order record
                                            Order.objects.create(
                                                bag=item.bag,
                                                customer=customer,
                                                status='reserved',
                                                stripe_session_id=session_id,
                                                payment_intent_id=session.payment_intent,
                                                total_cents=item.total_cents(),
                                                quantity=item.quantity
                                            )
                                            # Update bag status if needed
                                            if item.bag.status == 'listed':
                                                item.bag.status = 'reserved'
                                                item.bag.save(update_fields=['status'])
                                    
                                    # Clear cart INSIDE transaction to ensure it happens atomically
                                    CartItem.objects.filter(cart=cart).delete()
                                    
                                messages.success(self.request, "Payment successful! Your order has been processed.")
                            except Exception as e:
                                messages.error(self.request, f"Error processing order: {str(e)}")
            except Exception as e:
                messages.error(self.request, f"Error processing order: {str(e)}")
        
        return context


class CancelledView(TemplateView):
    """Cancellation page"""
    template_name = 'market/checkout_cancelled.html'



