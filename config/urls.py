# File location: lastbite-backend\config\urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings                 
from django.conf.urls.static import static 
from users.views_auth import dashboard_router     

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("landing.urls", "landing"), namespace="landing")),
    path("users/", include(("users.urls", "users"), namespace="users")),
    path("biz/", include(("business.urls", "business"), namespace="business")),
    path("market/", include(("market.urls", "market"), namespace="market")), 
    path("user-dashboard/", include(("dashboard.urls", "dashboard"), namespace="dashboard")),
    path("dashboard/", dashboard_router, name="dashboard"),
    path("market/", include(("market.urls", "market"), namespace="market")), #added in the market/cart feature
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    if getattr(settings, "MEDIA_URL", None):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)