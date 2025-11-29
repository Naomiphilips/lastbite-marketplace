from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse 
from users.forms_business import BusinessRegistrationForm

def register_business(request):
    if request.method != "POST":
        return redirect("landing:index")

    form = BusinessRegistrationForm(request.POST)
    if form.is_valid():
        try:
            form.save()
        except IntegrityError:
            form.add_error("business_email", "An account with this email already exists.")
        else:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "ok": True,
                    "redirect": reverse("business:dashboard"),
                })

            return redirect("business:dashboard")

    ctx = {"business_form": form, "open_business_modal": True}

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    return render(request, "landing/index.html", ctx)
