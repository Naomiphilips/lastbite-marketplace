# File location: landing/views.py

from django.shortcuts import render
from users.forms_business import BusinessRegistrationForm

def index(request):
    open_success = request.session.pop("open_business_success_modal", False)
    open_login = request.session.pop("open_login_modal", False)
    login_errors = request.session.pop("login_errors", {})
    login_username = request.session.pop("login_username", "")

    return render(request, "landing/index.html", {
      "business_form": BusinessRegistrationForm(),
      "open_business_modal": False,
      "open_business_success_modal": open_success,
      "open_login_modal": open_login,
      "login_errors": login_errors,
      "login_username": login_username,
    })
    """
    Landing page view - main homepage for LastBite
    """
    context = {
        'page_title': 'LastBite - Fight Food Waste, Save Money',
    }
    return render(request, 'landing/index.html', context)
