from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CheckoutForm, RegisterForm
from .models import Category, MenuItem, Order, OrderItem, SiteSetting


def home(request):
    featured = MenuItem.objects.filter(is_available=True, is_featured=True)[:6]
    return render(request, "restaurant/home.html", {"featured": featured})


def menu(request):
    categories = Category.objects.prefetch_related(
        Prefetch("items", queryset=MenuItem.objects.filter(is_available=True))
    )
    return render(request, "restaurant/menu.html", {"categories": categories})


def register(request):
    if request.user.is_authenticated:
        return redirect("restaurant:account")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("restaurant:account")
    return render(request, "restaurant/register.html", {"form": form})


@login_required
def account(request):
    orders = request.user.orders.prefetch_related("items")
    bookings = request.user.bookings.all()
    return render(request, "restaurant/account.html", {"orders": orders, "bookings": bookings})


# ---------- Cart ----------

def _parse_qty(value, default=1):
    try:
        qty = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(qty, 20))


def build_cart(request):
    """Return (lines, total) from the session cart."""
    cart = request.session.get("cart", {})
    items = MenuItem.objects.filter(id__in=cart.keys(), is_available=True)
    lines = []
    total = Decimal("0.00")
    for item in items:
        qty = cart[str(item.id)]
        line_total = item.price * qty
        total += line_total
        lines.append({"item": item, "qty": qty, "line_total": line_total})
    return lines, total


def cart_detail(request):
    lines, total = build_cart(request)
    return render(request, "restaurant/cart.html", {"lines": lines, "total": total})


@require_POST
def cart_add(request):
    item = get_object_or_404(MenuItem, pk=request.POST.get("item_id"), is_available=True)
    qty = _parse_qty(request.POST.get("qty"), default=1) or 1
    cart = request.session.get("cart", {})
    key = str(item.id)
    cart[key] = min(cart.get(key, 0) + qty, 20)
    request.session["cart"] = cart
    return redirect("restaurant:cart")


@require_POST
def cart_update(request):
    key = str(request.POST.get("item_id"))
    qty = _parse_qty(request.POST.get("qty"), default=1)
    cart = request.session.get("cart", {})
    if key in cart:
        if qty <= 0:
            del cart[key]
        else:
            cart[key] = qty
        request.session["cart"] = cart
    return redirect("restaurant:cart")


# ---------- Checkout ----------

@login_required
def checkout(request):
    site = SiteSetting.objects.first()
    if site and not site.accepting_orders:
        messages.error(request, "Sorry, we are not taking online orders right now.")
        return redirect("restaurant:cart")

    lines, total = build_cart(request)
    if not lines:
        return redirect("restaurant:cart")

    form = CheckoutForm(request.POST or None, initial={"customer_name": request.user.get_username()})
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                customer_name=data["customer_name"],
                phone=data["phone"],
                pickup_time=data["pickup_time"],
                payment_method=data["payment_method"],
                notes=data["notes"],
                total=total,
            )
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        menu_item=line["item"],
                        item_name=line["item"].name,
                        unit_price=line["item"].price,
                        quantity=line["qty"],
                    )
                    for line in lines
                ]
            )
        request.session["cart"] = {}
        return redirect("restaurant:order_success", order_id=order.id)

    return render(request, "restaurant/checkout.html", {"form": form, "lines": lines, "total": total})


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, "restaurant/order_success.html", {"order": order})

from .forms import BookingForm


def book_table(request):
    form = BookingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        if request.user.is_authenticated:
            booking.user = request.user
        booking.save()
        return redirect("restaurant:booking_done")
    return render(request, "restaurant/booking.html", {"form": form})


def booking_done(request):
    return render(request, "restaurant/booking_done.html")

import json

from django.core.cache import cache
from django.http import JsonResponse

from .gemini_service import GeminiError, ask_gemini


def _assistant_system_prompt():
    site = SiteSetting.objects.first()
    dishes = MenuItem.objects.filter(is_available=True).select_related("category")
    menu_lines = []
    for d in dishes:
        line = f"- {d.name}"
        if d.name_ga:
            line += f" ({d.name_ga})"
        line += f" | {d.category.name} | €{d.price}"
        if d.description:
            line += f" | {d.description}"
        menu_lines.append(line)

    return (
        "You are the friendly website assistant for Blasda Bistro, a traditional Irish restaurant. "
        "Answer ONLY using the restaurant information below. If the answer is not there, say you are not sure "
        "and suggest the customer phone or email the restaurant. Never invent dishes, prices, opening hours, "
        "ingredients or allergen information. For any allergy or dietary question, tell the customer to contact "
        "the restaurant directly. Reply in the language the customer writes in (English or Irish). "
        "Keep answers short (2 to 4 sentences). Online ordering is on the Menu page (takeaway with scheduled "
        "pickup) and table reservations are on the Book a table page.\n\n"
        f"Restaurant: {site.restaurant_name if site else 'Blasda Bistro'}\n"
        f"Address: {site.address if site else ''}\n"
        f"Phone: {site.phone if site else ''}\n"
        f"Email: {site.email if site else ''}\n"
        f"Opening hours:\n{site.opening_hours if site else ''}\n"
        f"Accepting online orders: {'yes' if (site and site.accepting_orders) else 'no'}\n\n"
        "Menu:\n" + ("\n".join(menu_lines) or "(menu not published yet)")
    )


@require_POST
def assistant_chat(request):
    # Rate limit: 10 messages per minute per visitor
    ip = request.META.get("REMOTE_ADDR", "unknown")
    key = f"assistant:{ip}"
    cache.add(key, 0, 60)
    if cache.incr(key) > 10:
        return JsonResponse(
            {"reply": "You are sending messages very quickly. Please wait a minute and try again."},
            status=429,
        )

    try:
        payload = json.loads(request.body)
    except ValueError:
        return JsonResponse({"reply": "Sorry, something went wrong."}, status=400)

    message = str(payload.get("message", "")).strip()[:500]
    if not message:
        return JsonResponse({"reply": "Please type a question."}, status=400)

    lines = []
    for h in (payload.get("history") or [])[-6:]:
        if isinstance(h, dict) and h.get("role") in ("user", "assistant"):
            who = "Customer" if h["role"] == "user" else "Assistant"
            lines.append(f"{who}: {str(h.get('content', ''))[:500]}")
    lines.append(f"Customer: {message}")
    prompt = "\n".join(lines) + "\nAssistant:"

    try:
        reply = ask_gemini(prompt, system=_assistant_system_prompt(), max_tokens=600)
    except GeminiError:
        site = SiteSetting.objects.first()
        phone = site.phone if site and site.phone else "us"
        return JsonResponse(
            {"reply": f"Sorry, our assistant is unavailable right now. Please call {phone}."},
            status=503,
        )
    return JsonResponse({"reply": reply or "Sorry, I could not find an answer to that."})