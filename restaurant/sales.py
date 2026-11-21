from decimal import Decimal

from django.db.models import Count, Q, Sum

from .models import DailySalesLog, Order


def refresh_daily_log(day):
    """Recalculate the ledger row for one calendar day (Irish time)."""
    orders = Order.objects.filter(created_at__date=day)
    stats = orders.aggregate(
        n_orders=Count("id"),
        n_completed=Count("id", filter=Q(status=Order.Status.COMPLETED)),
        n_cancelled=Count("id", filter=Q(status=Order.Status.CANCELLED)),
        revenue_sum=Sum("total", filter=~Q(status=Order.Status.CANCELLED)),
    )
    if not stats["n_orders"]:
        DailySalesLog.objects.filter(date=day).delete()
        return
    DailySalesLog.objects.update_or_create(
        date=day,
        defaults={
            "total_orders": stats["n_orders"],
            "completed_orders": stats["n_completed"],
            "cancelled_orders": stats["n_cancelled"],
            "total_revenue": stats["revenue_sum"] or Decimal("0.00"),
        },
    )