# dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.user_dashboard, name='user_dashboard'),

    # Map API endpoints
    path('api/nearby-listings/', views.get_nearby_listings, name='get_nearby_listings'),
    path('api/nearby-businesses/', views.get_nearby_businesses, name='get_nearby_businesses'),
    path('api/geocode-zipcode/', views.geocode_zipcode, name='geocode_zipcode'),
    path('api/stats/', views.get_dashboard_stats, name='get_dashboard_stats'),

    path('product/<int:product_id>/', views.view_product, name='view_product'),
]