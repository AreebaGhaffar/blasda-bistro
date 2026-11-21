from datetime import timedelta

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Order


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(max_length=120, label="Your name")
    phone = forms.CharField(max_length=30, label="Phone number")
    pickup_time = forms.DateTimeField(
        label="Pickup time",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
    )
    payment_method = forms.ChoiceField(choices=Order.PaymentMethod.choices, label="Payment")
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, label="Notes (allergies, requests)")

    def clean_pickup_time(self):
        value = self.cleaned_data["pickup_time"]
        if value < timezone.now() + timedelta(minutes=30):
            raise forms.ValidationError("Please choose a pickup time at least 30 minutes from now.")
        return value

from django.utils import timezone as _tz

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ("name", "phone", "email", "date", "time", "guests", "notes")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
            "guests": forms.NumberInput(attrs={"min": 1, "max": 20}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {"name": "Your name", "notes": "Special requests (allergies, birthday...)"}

    def clean_date(self):
        value = self.cleaned_data["date"]
        if value < _tz.localdate():
            raise forms.ValidationError("Please choose today or a future date.")
        return value

    def clean_guests(self):
        guests = self.cleaned_data["guests"]
        if guests < 1 or guests > 20:
            raise forms.ValidationError("We take bookings for 1 to 20 guests online. For bigger groups, please call us.")
        return guests

    def clean(self):
        cleaned = super().clean()
        d, t = cleaned.get("date"), cleaned.get("time")
        if d and t:
            from datetime import datetime
            when = _tz.make_aware(datetime.combine(d, t))
            if when < _tz.now():
                raise forms.ValidationError("Please choose a time in the future.")
        return cleaned