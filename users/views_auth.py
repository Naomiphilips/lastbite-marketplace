# users/views_user.py
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

def _safe_next_redirect(request, next_url: str):
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return None

def _role_target_url(user) -> str:
    """
    Default to the customer dashboard unless the user is a business user.
    Solves issue with redirecting business to user dashboard unless stated otherwise.
    """
    is_business = (
        user.groups.filter(name="BUSINESS").exists()
        or getattr(user, "is_business", False)   
    )
    if is_business:
        return reverse("business:dashboard")         
    return reverse("dashboard:user_dashboard") 

def login_modal(request):
    if request.method != "POST":
        request.session["open_login_modal"] = True
        return redirect("landing:index")

    form = AuthenticationForm(request, data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)

        request.session.pop("open_login_modal", None)
        request.session.pop("login_errors", None)

        next_url = request.POST.get("next") or request.GET.get("next")
        resp = _safe_next_redirect(request, next_url)
        if resp:
            return resp

        return redirect(_role_target_url(user))

    request.session["open_login_modal"] = True
    request.session["login_errors"] = {
        "non_field": list(form.non_field_errors()),
        "username": list(form.errors.get("username", [])),
        "password": list(form.errors.get("password", [])),
    }
    return redirect("landing:index")

def logout_view(request):
    logout(request)
    request.session.pop("open_login_modal", None)
    request.session.pop("login_errors", None)
    next_url = request.POST.get("next") or request.GET.get("next")
    resp = _safe_next_redirect(request, next_url)
    return resp or redirect("landing:index")

@login_required
def dashboard_router(request):
    """Direct user to proper dashboard"""
    target = _role_target_url(request.user)
   
    if request.path == target:
        return redirect("landing:index")
    return redirect(target)
