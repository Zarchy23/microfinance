from django import forms
from .models import LoanApplication
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import re
from django.core.exceptions import ValidationError

def validate_national_id(value):
    # Example simple pattern: allow alphanumeric between 5 and 20 chars (customize as needed)
    if not re.match(r'^[A-Za-z0-9-]{5,20}$', value):
        raise ValidationError('National ID must be 5-20 chars, letters, numbers or hyphens.')

def validate_phone(value):
    # Zimbabwe phone example: +2637XXXXXXXX or 07XXXXXXXX
    if not re.match(r'^(\+2637\d{8}|07\d{8})$', value):
        raise ValidationError('Phone must be +2637XXXXXXXX or 07XXXXXXXX.')

class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model = LoanApplication
        fields = ['amount','term_months','purpose','annual_income','existing_debt']
    def clean_amount(self):
        amt = self.cleaned_data['amount']
        if amt <= 0:
            raise forms.ValidationError('Amount must be positive.')
        return amt
    def clean_term_months(self):
        t = self.cleaned_data['term_months']
        if t <= 0:
            raise forms.ValidationError('Term must be at least 1 month.')
        return t

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    national_id = forms.CharField(max_length=50, validators=[validate_national_id])
    phone = forms.CharField(max_length=20, required=False, validators=[validate_phone])
    class Meta:
        model = User
        fields = ('username','email','first_name','last_name','password1','password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Email already in use.')
        return email

    def clean_national_id(self):
        nid = self.cleaned_data['national_id']
        from .models import Client
        if Client.objects.filter(national_id__iexact=nid).exists():
            raise forms.ValidationError('National ID already registered.')
        return nid
