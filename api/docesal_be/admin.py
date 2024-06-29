from django.contrib import admin
from .models import Product, UserProfile, Purchase, LogEntry

# Register your models here.
admin.site.register(Product)
admin.site.register(UserProfile)
admin.site.register(Purchase)
admin.site.register(LogEntry)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "level", "module", "message")
    list_filter = ("level", "timestamp")
    search_fields = ("message", "module")
