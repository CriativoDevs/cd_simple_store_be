from django.urls import path
from django.template.response import TemplateResponse
from django.contrib import admin

from .models import Product, UserProfile, Purchase, AccessLog


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "quantity", "was_bought", "created_at")
    readonly_fields = ("created_at",)


# Register your models here.
admin.site.register(AccessLog)
admin.site.register(Product)
admin.site.register(UserProfile)
admin.site.register(Purchase, PurchaseAdmin)
