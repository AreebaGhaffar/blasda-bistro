from decimal import Decimal

from django.conf import settings
from django.db import models


class SiteSetting(models.Model):
    """Single row the owner edits in the admin: contact info, hours, Irish story text."""
    restaurant_name = models.CharField(max_length=120, default="Blasda Bistro")
    tagline_en = models.CharField(max_length=200, blank=True)
    tagline_ga = models.CharField("Tagline (Irish)", max_length=200, blank=True)
    hero_title = models.CharField("Home page heading", max_length=120, default="Céad Míle Fáilte")
    hero_button = models.CharField("Home page button text", max_length=40, default="View our menu")
    story_en = models.TextField("Our story (English)", blank=True)
    story_ga = models.TextField("Our story (Irish)", blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    opening_hours = models.TextField(
        blank=True, help_text="One line per day, e.g. Mon-Fri: 12:00 - 21:00"
    )
    accepting_orders = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Site setting"
        verbose_name_plural = "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce a single row
        super().save(*args, **kwargs)

    def __str__(self):
        return self.restaurant_name


class Category(models.Model):
    name = models.CharField(max_length=80)
    name_ga = models.CharField("Name (Irish)", max_length=80, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="items")
    name = models.CharField(max_length=120)
    name_ga = models.CharField("Name (Irish)", max_length=120, blank=True)
    description = models.TextField(blank=True)
    description_ga = models.TextField("Description (Irish)", blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    image = models.ImageField(upload_to="menu/", blank=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category__sort_order", "name"]

    def __str__(self):
        return f"{self.name} (€{self.price})"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready for pickup"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Pay at pickup"
        CARD = "card", "Card"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    pickup_time = models.DateTimeField(help_text="Scheduled takeaway time")
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    is_paid = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=120)  # snapshot so old orders stay correct
    unit_price = models.DecimalField(max_digits=7, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.item_name}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings"
    )
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    date = models.DateField()
    time = models.TimeField()
    guests = models.PositiveIntegerField(default=2)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time"]

    def __str__(self):
        return f"{self.name} - {self.date} {self.time} ({self.guests})"


class DailySalesLog(models.Model):
    """One row per day: the audit ledger the owner reads."""
    date = models.DateField(unique=True)
    total_orders = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=11, decimal_places=2, default=Decimal("0.00"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date}: €{self.total_revenue}"