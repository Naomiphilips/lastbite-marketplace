# File location: dashboard/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from business.models import Listing, Product
from users.models import BusinessRegistration, CustomerProfile
from market.models import Order, Cart
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
import math
import requests

User = get_user_model()

@login_required
def user_dashboard(request):
    # Initialize default values
    total_cart_items = 0  
    total_spent = 0.0
    cart_subtotal = 0.0
    favorites_count = 0
    
    # Get customer profile if exists
    try:
        customer_profile = CustomerProfile.objects.get(user=request.user)
        
        # Get total items in cart (sum of all quantities)
        # CHANGED: Count items in current cart instead of completed orders
        try:
            cart = Cart.objects.get(customer=customer_profile)
            # Sum all quantities from cart items
            total_cart_items = cart.items.aggregate(
                total=Sum('quantity')
            )['total'] or 0
            # Get cart subtotal
            cart_subtotal = cart.total_cents() / 100  # Convert cents to dollars
        except Cart.DoesNotExist:
            total_cart_items = 0
            cart_subtotal = 0.0
        
        # Get total amount spent (sum of all completed orders)
        total_spent_cents = Order.objects.filter(
            customer=customer_profile,
            total_cents__isnull=False
        ).aggregate(total=Sum('total_cents'))['total'] or 0
        total_spent = total_spent_cents / 100  # Convert cents to dollars
            
    except CustomerProfile.DoesNotExist:
        # User doesn't have a customer profile yet
        pass
    
    context = {
        'page_title': 'Dashboard - LastBite',
        'user': request.user,
        'total_cart_items': total_cart_items,  
        'total_spent': total_spent,
        'cart_subtotal': cart_subtotal,
        'favorites_count': favorites_count,
    }
    return render(request, 'dashboard/user_dashboard.html', context)


@login_required
@require_http_methods(["GET"])
def get_nearby_listings(request):
    """
    Get listings near a specific location
    Query params: lat, lng, radius (in km, default 10)
    """
    try:
        user_lat = float(request.GET.get('lat'))
        user_lng = float(request.GET.get('lng'))
        radius = float(request.GET.get('radius', 10))  
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)
    
    # Get all listings with location data
    products = Product.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        quantity__gt=0,  # Only show available items
        status="listed"
    )
    
    nearby_products = []
    
    for product in products:
        # Calculate distance using Haversine formula
        distance = calculate_distance(
            user_lat, user_lng, 
            float(product.latitude), float(product.longitude)
        )
        
        if distance <= radius:
            nearby_products.append({
                'id': product.id,
                'title': product.title,
                'price': str(product.base_price),
                'quantity': product.quantity,
                'notes': product.description or product.notes or '',
                'image': product.image.url if product.image else None,
                'address': product.address,
                'city': product.city,
                'state': product.state,
                'zip_code': product.zip_code,
                'latitude': float(product.latitude),
                'longitude': float(product.longitude),
                'distance': round(distance, 2),
                'owner_name': product.owner.get_full_name() or product.owner.username
            })
    
    # Sort by distance
    nearby_products.sort(key=lambda x: x['distance'])
    
    return JsonResponse({
        'success': True,
        'count': len(nearby_products),
        'listings': nearby_products
    })


@login_required
@require_http_methods(["GET"])
def get_nearby_businesses(request):
    """
    Get businesses (grouped by owner with listings) near a specific location
    Query params: lat, lng, radius (in km, default 10)
    """
    try:
        user_lat = float(request.GET.get('lat'))
        user_lng = float(request.GET.get('lng'))
        radius = float(request.GET.get('radius', 10))  # Default 10km
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)
    
    # Get all listings with location data and available quantity
    products = Product.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        quantity__gt=0,
        status="listed"
    ).select_related('owner')
    
    # Group listings by owner and calculate distances
    businesses_dict = {}
    
    for product in products:
        # Calculate distance
        distance = calculate_distance(
            user_lat, user_lng,
            float(product.latitude), float(product.longitude)
        )
        
        # Only include if within radius
        if distance <= radius:
            owner_id = product.owner.id
            
            # Get BusinessRegistration ID for this owner
            business_registration = BusinessRegistration.objects.filter(user=product.owner).first()
            business_reg_id = business_registration.id if business_registration else None
            
            # Skip if no business registration found
            if not business_reg_id:
                continue
            
            # Initialize business entry if not exists
            if owner_id not in businesses_dict:
                # Use the first listing's location as the business location
                businesses_dict[owner_id] = {
                    'owner_id': owner_id,
                    'business_id': business_reg_id,
                    'owner_name': product.owner.get_full_name() or product.owner.username,
                    'owner_username': product.owner.username,
                    'latitude': float(product.latitude),
                    'longitude': float(product.longitude),
                    'address': product.address,
                    'city': product.city,
                    'state': product.state,
                    'zip_code': product.zip_code,
                    'distance': distance,
                    'product_count': 0,
                    'products': []
                }
            
            # Add listing to this business
            businesses_dict[owner_id]['product_count'] += 1
            businesses_dict[owner_id]['products'].append({
                'id': product.id,
                'title': product.title,
                'price': str(product.base_price),
                'image': product.image.url if product.image else None,
            })
            
            # Update distance if this listing is closer
            if distance < businesses_dict[owner_id]['distance']:
                businesses_dict[owner_id]['distance'] = distance
                businesses_dict[owner_id]['latitude'] = float(product.latitude)
                businesses_dict[owner_id]['longitude'] = float(product.longitude)
                businesses_dict[owner_id]['address'] = product.address
                businesses_dict[owner_id]['city'] = product.city
                businesses_dict[owner_id]['state'] = product.state
                businesses_dict[owner_id]['zip_code'] = product.zip_code
    
    # Convert to list and sort by distance
    businesses_list = list(businesses_dict.values())
    businesses_list.sort(key=lambda x: x['distance'])
    
    # Round distances
    for business in businesses_list:
        business['distance'] = round(business['distance'], 2)
    
    return JsonResponse({
        'success': True,
        'count': len(businesses_list),
        'businesses': businesses_list
    })


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


@login_required
@require_http_methods(["POST"])
def geocode_zipcode(request):
    """
    Convert zip code to coordinates using Nominatim (OpenStreetMap)
    """
    zip_code = request.POST.get('zip_code')
    
    if not zip_code:
        return JsonResponse({'error': 'Zip code required'}, status=400)
    
    # Use Nominatim API (free, no API key needed)
    url = f"https://nominatim.openstreetmap.org/search"
    params = {
        'postalcode': zip_code,
        'country': 'US',  # Adjust if needed
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'LastBite-App/1.0'  # Required by Nominatim
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        if data and len(data) > 0:
            return JsonResponse({
                'success': True,
                'latitude': float(data[0]['lat']),
                'longitude': float(data[0]['lon']),
                'display_name': data[0].get('display_name', '')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Zip code not found'
            }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Geocoding failed: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_dashboard_stats(request):
    """
    API endpoint to get real-time dashboard statistics
    Returns: JSON with total_cart_items, total_spent, cart_subtotal, favorites_count
    """
    stats = {
        'total_cart_items': 0, 
        'total_spent': 0.0,
        'cart_subtotal': 0.0,
        'favorites_count': 0,
    }
    
    try:
        customer_profile = CustomerProfile.objects.get(user=request.user)
        
        # Total items in cart (sum of quantities)
        # CHANGED: Count cart items instead of orders
        try:
            cart = Cart.objects.get(customer=customer_profile)
            stats['total_cart_items'] = cart.items.aggregate(
                total=Sum('quantity')
            )['total'] or 0
            stats['cart_subtotal'] = round(cart.total_cents() / 100, 2)
        except Cart.DoesNotExist:
            stats['total_cart_items'] = 0
            stats['cart_subtotal'] = 0.0
        
        # Total spent
        total_spent_cents = Order.objects.filter(
            customer=customer_profile,
            total_cents__isnull=False
        ).aggregate(total=Sum('total_cents'))['total'] or 0
        stats['total_spent'] = round(total_spent_cents / 100, 2)
            
    except CustomerProfile.DoesNotExist:
        pass
    
    return JsonResponse({
        'success': True,
        'stats': stats
    })
    
@login_required
@require_http_methods(["GET"])
def view_product(request, product_id):
    """
    Display detailed view of a single product
    """
    try:
        product = Product.objects.get(id=product_id, status="listed")
    except Product.DoesNotExist:
        return render(request, '404.html', {'message': 'Product not found'}, status=404)
    
    # Get seller info
    seller = product.owner
    business_registration = BusinessRegistration.objects.filter(user=seller).first()
    
    context = {
        'page_title': f'{product.title} - LastBite',
        'product': product,
        'seller': seller,
        'business_registration': business_registration,
        'is_owner': request.user == seller,
    }
    
    return render(request, 'dashboard/view_product.html', context)
