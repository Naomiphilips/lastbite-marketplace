from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import re


User = get_user_model()
EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
    )
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email',) 

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not EMAIL_REGEX.match(email):
            raise ValidationError('Please enter a valid email address.')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email'].lower()

        if hasattr(user, 'email'):
            user.email = email

        if hasattr(user, 'username'):
            user.username = email

        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
        return user

class StrictPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        User = get_user_model()
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError(_("Invalid email"))
        return email