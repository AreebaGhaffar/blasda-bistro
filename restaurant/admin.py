import json

from django.contrib import admin, messages

from .gemini_service import GeminiError, ask_gemini
from .models import (
    Booking,
    Category,
    DailySalesLog,
    MenuItem,
    Order,
    OrderItem,
    SiteSetting,
)

admin.site.site_header = "Blasda Bistro Admin"
admin.site.site_title = "Blasda Bistro"
admin.site.index_title = "Manage your restaurant"


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Restaurant", {"fields": ("restaurant_name", "accepting_orders")}),
        ("Taglines", {"fields": ("tagline_en", "tagline_ga")}),
        ("Our story", {"fields": ("story_en", "story_ga")}),
        ("Contact and hours", {"fields": ("phone", "email", "address", "opening_hours")}),
    )

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "name_ga", "sort_order")
    list_editable = ("sort_order",)


AI_SYSTEM = (
    "You write menu copy for Blasda Bistro, a warm, traditional Irish restaurant that "
    "serves fresh local farm-to-table food. You reply with valid JSON only, no extra text."
)


@admin.action(description="Generate descriptions with AI (English + Irish)")
def generate_ai_descriptions(modeladmin, request, queryset):
    done, failed = 0, []
    for item in queryset:
        prompt = (
            f"Dish name: {item.name}\n"
            f"Category: {item.category.name}\n"
            f"Existing notes from the owner: {item.description or 'none'}\n\n"
            "Return a JSON object with exactly these keys:\n"
            '"description_en": an appetising English description, 1 to 2 sentences, max 35 words,\n'
            '"description_ga": the same description in natural Irish (Gaeilge),\n'
            '"name_ga": the dish name in Irish.\n'
            "Do not invent allergens, prices or ingredients that are not implied by the dish name or notes."
        )
        try:
            raw = ask_gemini(prompt, system=AI_SYSTEM, max_tokens=1000)
            cleaned = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            item.description = data["description_en"].strip()
            item.description_ga = data["description_ga"].strip()
            if data.get("name_ga"):
                item.name_ga = data["name_ga"].strip()
            item.save()
            done += 1
        except (GeminiError, ValueError, KeyError, TypeError):
            failed.append(item.name)

    if done:
        modeladmin.message_user(
            request,
            f"AI wrote descriptions for {done} dish(es). Please proofread the Irish before publishing.",
            messages.SUCCESS,
        )
    if failed:
        modeladmin.message_user(
            request,
            "Could not generate for: " + ", ".join(failed) + ". Please try again.",
            messages.WARNING,
        )


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_available", "is_featured")
    list_editable = ("price", "is_available", "is_featured")
    list_filter = ("category", "is_available", "is_featured")
    search_fields = ("name", "name_ga", "description")
    actions = [generate_ai_descriptions]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("item_name", "unit_price", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "pickup_time", "status", "payment_method", "is_paid", "total", "created_at")
    list_editable = ("status", "is_paid")
    list_filter = ("status", "payment_method", "is_paid", "created_at")
    search_fields = ("customer_name", "phone")
    inlines = [OrderItemInline]
    readonly_fields = ("total", "created_at")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "time", "guests", "phone", "status")
    list_editable = ("status",)
    list_filter = ("status", "date")
    search_fields = ("name", "phone", "email")


@admin.register(DailySalesLog)
class DailySalesLogAdmin(admin.ModelAdmin):
    list_display = ("date", "total_orders", "completed_orders", "cancelled_orders", "total_revenue")
    readonly_fields = ("date", "total_orders", "completed_orders", "cancelled_orders", "total_revenue", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False