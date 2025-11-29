import re
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.models import Group            # 👈 NEW
from django.db import transaction                       # 👈 NEW
from .models_businessreg import BusinessRegistration

User = get_user_model()

#added in the state abbreviations for more proper address input
US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA",
    "ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK",
    "OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC"
}
ADDR_RE = re.compile(
    r"""^\s*
        (?P<num>\d+)\s+            # street number
        (?P<street>[^,]+),\s*      # street name until comma
        (?P<city>[^,]+),\s*        # city until comma
        (?P<state>[A-Za-z]{2})     # 2-letter state
        (?:\s+(?P<zip>\d{5}(?:-\d{4})?))?  # optional ZIP or ZIP+4
        \s*$""",
    re.VERBOSE,
)
DIGITS_RE = re.compile(r"\D+")

class BusinessRegistrationForm(forms.Form):
    business_name = forms.CharField(label="Business Name", max_length=120)
    business_type = forms.ChoiceField(choices=BusinessRegistration.BUSINESS_TYPE_CHOICES)
    business_address = forms.CharField(label="Business Address", max_length=255)
    phone_number = forms.CharField(label="Phone Number", max_length=15)
    business_email = forms.EmailField(label="Business Email")
    owner_name = forms.CharField(label="Owner Name", max_length=120)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    agree_terms = forms.BooleanField(label="I agree to the Business Terms & Conditions")

    def clean_business_address(self):
        addr = self.cleaned_data.get("business_address", "").strip()
        if not addr:
            return addr
        m = ADDR_RE.match(addr)
        if not m:
            raise ValidationError('Must Follow Format, "123 Main St, Chicago, IL 60601" (Zipcode is optional).')
        state = m.group("state").upper()
        if state not in US_STATES:
            raise ValidationError("Enter a valid 2-letter US state (e.g., IL).")
        city = " ".join(w.capitalize() for w in m.group("city").strip().split())
        street = m.group("street").strip()
        zipc = m.group("zip") or ""
        normalized = f"{m.group('num')} {street}, {city}, {state}{(' ' + zipc) if zipc else ''}"
        self.cleaned_data["business_address"] = normalized
        return normalized

#limits on phine length and validation
    def clean_phone_number(self):
        raw = self.cleaned_data["phone_number"]
        digits = DIGITS_RE.sub("", raw)
        if not digits:
            raise ValidationError("Phone number cannot be empty.")
        if len(digits) > 15:
            raise ValidationError("Phone number must be at most 15 digits.")
        return digits
#display error if email is in use.
    def clean_business_email(self):
        email = self.cleaned_data["business_email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        if BusinessRegistration.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_password(self):
        pwd = self.cleaned_data["password"]
        password_validation.validate_password(pwd)
        return pwd

    @transaction.atomic                         
    def save(self):
        cd = self.cleaned_data
        email = cd["business_email"]
        pwd = cd["password"]

        kwargs = {User.USERNAME_FIELD: email}
        if "email" in [f.name for f in User._meta.get_fields()]:
            kwargs["email"] = email

        user = User.objects.create_user(password=pwd, **kwargs)

        if hasattr(user, "first_name"):
            user.first_name = cd.get("owner_name", "")
            user.save(update_fields=["first_name"])

        biz = BusinessRegistration.objects.create(
            user=user,
            name=cd["business_name"],
            business_type=cd["business_type"],
            address=cd["business_address"],
            phone_number=cd["phone_number"],
            email=email,
            owner_name=cd["owner_name"],
        )

       
        business_group, _ = Group.objects.get_or_create(name="BUSINESS")
        user.groups.add(business_group)
        
        user.groups.remove(*user.groups.filter(name="CUSTOMER"))

        return biz
