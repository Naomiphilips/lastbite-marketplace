# users/urls.py

from django.urls import path, reverse_lazy
from . import views_auth
from . import view_business, views
from django.contrib.auth import views as auth_views
from .views import RegisterView
from .forms import StrictPasswordResetForm

app_name = "users"

urlpatterns = [
    path("biz/register/", view_business.register_business, name="business-register"),
    path("login/", views_auth.login_modal, name="login"),    
    path("logout/", views_auth.logout_view, name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("password_reset/",auth_views.PasswordResetView.as_view(template_name="users/password_reset.html",success_url=reverse_lazy("users:password_reset_done"),email_template_name="users/password_reset_email.html",form_class=StrictPasswordResetForm),name="password_reset",),
    path("password_reset/done/",auth_views.PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"),name="password_reset_done",),
    path("reset/<uidb64>/<token>/",auth_views.PasswordResetConfirmView.as_view(template_name="users/password_reset_confirm.html"),name="password_reset_confirm",),
    path("reset/done/",auth_views.PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"),name="password_reset_complete",),
    path("history/", views.user_history, name="user_history"),
]
