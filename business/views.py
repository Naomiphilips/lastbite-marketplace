# File location: business/views.py

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from users.models import BusinessRegistration
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse, HttpResponseForbidden

from .forms import ListingForm, ProductForm, BidForm
from .models import Listing, Product, Bid
from django.db.models import Prefetch
from django.contrib import messages
import requests

def is_business(u):
    return u.is_authenticated and u.groups.filter(name="BUSINESS").exists()


def geocode_address(address_string):
    """
    Geocode an address string to lat/lng using Nominatim (OpenStreetMap)
    Returns: dict with 'latitude', 'longitude', 'address', 'city', 'state', 'zip_code'
    """
    if not address_string or not address_string.strip():
        return None
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address_string,
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }
    headers = {
        'User-Agent': 'LastBite-App/1.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        if data and len(data) > 0:
            result = data[0]
            address_details = result.get('address', {})
            
            # Extract address components
            street_number = address_details.get('house_number', '')
            street = address_details.get('road', '')
            street_address = f"{street_number} {street}".strip() if street_number else street
            
            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'address': street_address or address_details.get('street', ''),
                'city': address_details.get('city') or address_details.get('town') or address_details.get('village', ''),
                'state': address_details.get('state', ''),
                'zip_code': address_details.get('postcode', '')
            }
    except Exception as e:
        print(f"Geocoding error: {e}")
    
    return None


def get_business_location(user):
    """
    Get location data from user's business registration
    Returns geocoded location dict or None
    """
    try:
        business = BusinessRegistration.objects.filter(user=user).first()
        if business and business.address:  # CHANGED: using 'address' field
            return geocode_address(business.address)
    except Exception as e:
        print(f"Error getting business location: {e}")
    
    return None


@login_required
@user_passes_test(is_business)
def dashboard(request):
   #displays an error if user does not have a business profile at the moemnt
    business = get_object_or_404(BusinessRegistration, user=request.user)

    #sends user to the new merged business page
    return redirect("business:business_public", business_id=business.id)


@login_required
@user_passes_test(is_business)
def profile(request):
    return render(request, "business/profile.html")


@login_required
@user_passes_test(is_business)
def listing_create(request):
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            
            # Automatically add location from business registration
            location_data = get_business_location(request.user)
            if location_data:
                listing.latitude = location_data['latitude']
                listing.longitude = location_data['longitude']
                listing.address = location_data['address']
                listing.city = location_data['city']
                listing.state = location_data['state']
                listing.zip_code = location_data['zip_code']
            else:
                messages.warning(request, "Could not geocode your business location. Listing will not appear on map.")
            
            listing.save()
            return redirect(f"{reverse('business:listing_detail', args=[listing.pk])}?created=1")
    else:
        form = ListingForm()
    return render(request, "business/listing_create.html", {"form": form})


@login_required
@user_passes_test(is_business)
def listing_list(request):
    items = Listing.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "business/listing_list.html", {"items": items})


@login_required
@user_passes_test(is_business)
def listing_detail(request, pk: int):
    item = get_object_or_404(Listing, pk=pk, owner=request.user)
    created = request.GET.get("created") == "1"
    return render(request, "business/listing_detail.html", {"item": item, "created": created})


@login_required
@user_passes_test(is_business)
def listing_edit(request, pk: int):
    item = get_object_or_404(Listing, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            listing = form.save(commit=False)
            
            # Update location data if it's missing
            if not listing.latitude or not listing.longitude:
                location_data = get_business_location(request.user)
                if location_data:
                    listing.latitude = location_data['latitude']
                    listing.longitude = location_data['longitude']
                    listing.address = location_data['address']
                    listing.city = location_data['city']
                    listing.state = location_data['state']
                    listing.zip_code = location_data['zip_code']
            
            listing.save()
            messages.success(request, "Listing updated successfully!")
            return redirect(reverse('business:listing_detail', args=[item.pk]))
    else:
        form = ListingForm(instance=item)
    return render(request, "business/listing_edit.html", {"form": form, "item": item})


@login_required
@user_passes_test(is_business)
def listing_delete(request, pk: int):
    item = get_object_or_404(Listing, pk=pk, owner=request.user)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Listing deleted successfully!")
        return redirect(reverse('business:listing_list'))
    return render(request, "business/listing_delete.html", {"item": item})


@login_required
@user_passes_test(is_business)
def product_create(request):
    """Create a new Product (unified model)"""
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.status = "listed"  # Set status to listed

            location_data = get_business_location(request.user)
            if location_data:
                product.latitude = location_data['latitude']
                product.longitude = location_data['longitude']
                product.address = location_data['address']
                product.city = location_data['city']
                product.state = location_data['state']
                product.zip_code = location_data['zip_code']
            else:
                messages.warning(request, "Could not geocode your business location. Product will not appear on map.")

            product.save()
            messages.success(request, "Product created successfully!")
            return redirect(f"{reverse('business:product_detail', args=[product.pk])}?created=1")
    else:
        form = ProductForm()
    return render(request, "business/product_create.html", {"form": form})

@login_required
@user_passes_test(is_business)
def product_list(request):
    """List all products for the business"""
    products = Product.objects.filter(owner=request.user, quantity__gt=0).order_by("-created_at")
    return render(request, "business/product_list.html", {"products": products})

@login_required
def product_detail_public(request, pk: int):
    """Public product detail view for customers"""
    product = get_object_or_404(Product, pk=pk, status="listed")
    
    # Auto-process expiration if needed (this will update status if expired)
    product.process_expiration_if_needed()
    
    # Refresh from DB if status changed
    if product.status != 'listed' or product.quantity <= 0:
        product.refresh_from_db()
        # If status changed, redirect or show appropriate message
        if product.status == 'expired':
            messages.info(request, "This product's bidding period has ended.")
        elif product.status == 'reserved':
            messages.info(request, "This product has been reserved for the winning bidder.")
        elif product.quantity <= 0:
            messages.info(request, "This product is out of stock.")
            return redirect('business:business_public', business_id=product.owner.business.id)
    
    # Get bidding info
    highest_bid = product.get_highest_bid()
    is_bidding_open = product.is_bidding_open()
    min_bid = product.get_minimum_bid() if is_bidding_open else None
    
    # Get winner info if bidding has ended
    winner = None
    if not is_bidding_open and product.enable_bidding:
        winner = product.get_winning_bidder()
    
    # Get user's bids on this product
    user_bids = []
    if request.user.is_authenticated:
        user_bids = Bid.objects.filter(product=product, bidder=request.user).order_by('-created_at')
    
    is_owner = request.user.is_authenticated and request.user == product.owner

    return render(request, "business/product_detail_public.html", {
        "product": product,
        "highest_bid": highest_bid,
        "is_bidding_open": is_bidding_open,
        "min_bid": min_bid,
        "user_bids": user_bids,
        "is_owner": is_owner,
        "winner": winner,
    })

@login_required
@user_passes_test(is_business)
def product_detail(request, pk: int):
    """View product details"""
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    created = request.GET.get("created") == "1"

    # Auto-process expiration if needed
    product.process_expiration_if_needed()
    product.refresh_from_db()

    is_customer = False
    if request.user.is_authenticated:
        is_customer = not request.user.groups.filter(name="BUSINESS").exists()

     # Get bidding info
    highest_bid = product.get_highest_bid()
    is_bidding_open = product.is_bidding_open()
    min_bid = product.get_minimum_bid() if is_bidding_open else None

    # Get winner info
    winner = None
    if not is_bidding_open and product.enable_bidding:
        winner = product.get_winning_bidder()

    # Get user's bids on this product
    user_bids = []
    if request.user.is_authenticated:
        user_bids = Bid.objects.filter(product=product, bidder=request.user).order_by('-created_at')

    return render(request, "business/product_detail.html", {
        "product": product,
        "created": created,
        "is_customer": is_customer,
        "highest_bid": highest_bid,
        "is_bidding_open": is_bidding_open,
        "min_bid": min_bid,
        "user_bids": user_bids,
        "winner": winner,
    })

@login_required
@user_passes_test(is_business)
def product_edit(request, pk: int):
    """Edit an existing product"""
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            
            # Update location data if it's missing
            if not product.latitude or not product.longitude:
                location_data = get_business_location(request.user)
                if location_data:
                    product.latitude = location_data['latitude']
                    product.longitude = location_data['longitude']
                    product.address = location_data['address']
                    product.city = location_data['city']
                    product.state = location_data['state']
                    product.zip_code = location_data['zip_code']

            product.save()
            messages.success(request, "Product updated successfully!")
            return redirect(reverse('business:product_detail', args=[product.pk]))
    else:
        form = ProductForm(instance=product)
    return render(request, "business/product_edit.html", {"form": form, "product": product})

@login_required
@user_passes_test(is_business)
def product_delete(request, pk: int):
    """Delete a product"""
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect(reverse('business:product_list'))
    return render(request, "business/product_delete.html", {"product": product})
    

@require_POST
@login_required
def place_bid(request, product_id: int):
    """Place a bid on a product"""
    product = get_object_or_404(Product, pk=product_id)
    
    # Auto-process expiration first
    product.process_expiration_if_needed()
    product.refresh_from_db()
    
    # Check if bidding is open (this will also process if needed)
    if not product.is_bidding_open():
        messages.error(request, "Bidding is not open for this product.")
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('business:product_detail_public', pk=product_id)
    
    form = BidForm(request.POST, product=product, user=request.user)
    
    if form.is_valid():
        bid = form.save(commit=False)
        bid.product = product
        bid.bidder = request.user
        bid.save()
        messages.success(request, f"Your bid of ${bid.amount:.2f} has been placed!")
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('business:product_detail_public', pk=product_id)
    else:
        for error in form.errors.values():
            messages.error(request, error[0])
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('business:product_detail_public', pk=product_id)

@login_required
@user_passes_test(is_business)
def bids(request):
    """View all bids on products owned by the business"""
    # Get all products owned by user
    products = Product.objects.filter(owner=request.user)
    
    # Get all bids on these products
    bids_list = Bid.objects.filter(product__in=products).select_related('product', 'bidder').order_by('-created_at')
    
    # Group bids by product
    bids_by_product = {}
    for bid in bids_list:
        if bid.product.id not in bids_by_product:
            bids_by_product[bid.product.id] = {
                'product': bid.product,
                'bids': []
            }
        bids_by_product[bid.product.id]['bids'].append(bid)
    
    context = {
        'bids_by_product': bids_by_product.values(),
        'total_bids': bids_list.count()
    }
    return render(request, "business/bids.html", context)

@login_required
def my_bids(request):
    """View all bids placed by the current user"""
    user_bids = Bid.objects.filter(bidder=request.user).select_related('product', 'product__owner').order_by('-created_at')
    
    context = {
        'bids': user_bids
    }
    return render(request, "business/my_bids.html", context)


@require_POST
@login_required
def update_description(request, business_id):
    business = get_object_or_404(BusinessRegistration, pk=business_id)

    if business.user != request.user:
        return JsonResponse({"error": "Permission denied"}, status=403)

    new_desc = request.POST.get("description", "").strip()
    business.description = new_desc
    business.save(update_fields=["description"])

    return JsonResponse({"success": True, "description": new_desc})

@login_required
def upload_business_logo(request, business_id: int):
    """Allow the business owner to upload/update their logo."""
    business = get_object_or_404(BusinessRegistration, pk=business_id)

    if business.user and business.user != request.user:
        return HttpResponseForbidden("You do not have permission to edit this business.")

    if request.method == "POST" and request.FILES.get("logo"):
        business.logo = request.FILES["logo"]
        business.save()
        return redirect("business:business_public", business_id=business.id)

    return redirect("business:business_public", business_id=business.id)

@login_required
def delete_business_logo(request, business_id: int):
    """Remove the business logo and reset to default."""
    business = get_object_or_404(BusinessRegistration, pk=business_id)

    # Only owner can edit
    if business.user and business.user != request.user:
        return HttpResponseForbidden("You do not have permission to edit this business.")

    if request.method == "POST":
        if business.logo:
            # delete file from storage but don't save yet
            business.logo.delete(save=False)
            business.logo = None
            business.save(update_fields=["logo"])
        return redirect("business:business_public", business_id=business.id)

    return redirect("business:business_public", business_id=business.id)


 
def business_public(request, business_id: int):
    """
    Public-facing business page.
    - Looks up BusinessRegistration by id
    - Uses its .user as the owner for listings
    - Shows 'best sellers' (top 5 most recent for now)
    - Shows active listings with pagination + 'View More' button
    """
    business = get_object_or_404(BusinessRegistration, pk=business_id)
    owner_user = business.user

    products_qs = (
        Product.objects.filter(owner=owner_user, status="listed", quantity__gt=0)
        .prefetch_related(
            Prefetch('bids', queryset=Bid.objects.select_related('bidder').order_by('-amount', '-created_at'))
        )
        .order_by("-created_at")
    )

    best_sellers = products_qs[:5]

    paginator = Paginator(products_qs, 6)
    page_number = request.GET.get("page", "1")
    page_obj = paginator.get_page(page_number)

    is_customer = False
    is_owner = False
    if request.user.is_authenticated:
        is_customer = not request.user.groups.filter(name="BUSINESS").exists()
        is_owner = (request.user == owner_user)

    context = {
        "business": business,
        "owner_user": owner_user,
        "best_sellers": best_sellers,
        "page_obj": page_obj,
        "has_more": page_obj.has_next(),
        "appname": "LastBite",
        "is_customer": is_customer,
        "is_owner": is_owner,
    }
    return render(request, "business/business_public.html", context)