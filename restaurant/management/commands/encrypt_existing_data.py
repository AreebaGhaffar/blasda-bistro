from django.core.management.base import BaseCommand

from restaurant.models import Booking, Order


class Command(BaseCommand):
    help = "Encrypts any customer data in the database that is still stored as plain text."

    def handle(self, *args, **options):
        orders = 0
        for order in Order.objects.all():
            order.save()
            orders += 1
        bookings = 0
        for booking in Booking.objects.all():
            booking.save()
            bookings += 1
        self.stdout.write(self.style.SUCCESS(f"Encrypted {orders} orders and {bookings} bookings."))