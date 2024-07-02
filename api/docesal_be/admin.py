from django.contrib import admin
from .models import Product, UserProfile, Purchase


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "quantity", "was_bought", "created_at")


# Register your models here.
admin.site.register(Product)
admin.site.register(UserProfile)
admin.site.register(Purchase, PurchaseAdmin)
