from .models import SiteSetting


def site_settings(request):
    cart = request.session.get("cart", {})
    return {
        "site": SiteSetting.objects.first(),
        "cart_count": sum(cart.values()),
    }