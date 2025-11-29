from django.urls import path
from . import views

app_name = "business"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("listings/new/", views.listing_create, name="listing_create"),
    path("listings/", views.listing_list, name="listing_list"),
    path("listings/<int:pk>/", views.listing_detail, name="listing_detail"),
    path("listings/<int:pk>/edit/", views.listing_edit, name="listing_edit"),
    path("listings/<int:pk>/delete/", views.listing_delete, name="listing_delete"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/", views.product_list, name="product_list"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("bids/", views.bids, name="bids"),
    path("public/<int:business_id>/", views.business_public, name="business_public"),
    path("public/<int:business_id>/update_description/", views.update_description, name="update_description"),
    path("public/<int:business_id>/upload-logo/", views.upload_business_logo, name="upload_business_logo"),
    path("public/<int:business_id>/delete-logo/", views.delete_business_logo, name="delete_business_logo"),
    path("products/<int:pk>/public/", views.product_detail_public, name="product_detail_public"),
    path("products/<int:product_id>/bid/", views.place_bid, name="place_bid"),
    path("my-bids/", views.my_bids, name="my_bids"),

]
