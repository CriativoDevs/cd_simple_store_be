from django.contrib import admin
from .models import Product, UserProfile, Purchase, AccessLog


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "quantity", "was_bought", "created_at")
    readonly_fields = ("created_at",)


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "ip_address", "user_agent")
    list_filter = ("timestamp", "ip_address")


# Register your models here.
admin.site.register(Product)
admin.site.register(UserProfile)
admin.site.register(Purchase, PurchaseAdmin)
