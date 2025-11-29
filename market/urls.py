# market/urls.py
from django.urls import path
from . import views

app_name = 'market'

urlpatterns = [
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),

    path("", views.dynamic_pricing, name="dynamic_pricing"),

    path('config/', views.stripe_config, name='stripe_config'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('checkout/success/', views.SuccessView.as_view(), name='checkout_success'),
    path('checkout/cancelled/', views.CancelledView.as_view(), name='checkout_cancelled'),
   #path("", views.dynamic_pricing, name="dynamic_pricing"),
    
]

