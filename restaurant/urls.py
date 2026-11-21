from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "restaurant"

urlpatterns = [
    path("", views.home, name="home"),
    path("menu/", views.menu, name="menu"),
    path("register/", views.register, name="register"),
    path("account/", views.account, name="account"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/<int:order_id>/", views.order_success, name="order_success"),
    path("book/", views.book_table, name="book"),
    path("book/thanks/", views.booking_done, name="booking_done"),
    path("assistant/", views.assistant_chat, name="assistant"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="restaurant/login.html", redirect_authenticated_user=True),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]