from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order
from .sales import refresh_daily_log


@receiver([post_save, post_delete], sender=Order)
def order_changed(sender, instance, **kwargs):
    refresh_daily_log(timezone.localtime(instance.created_at).date())