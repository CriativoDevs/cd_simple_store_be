from django.db import models
from django.contrib.auth.models import User
import logging


class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=100)
    product_image = models.ImageField(null=True, blank=True)
    product_brand = models.CharField(max_length=100, null=True, blank=True)
    product_category = models.CharField(max_length=100, null=True, blank=True)
    product_description = models.TextField(null=True, blank=True)
    product_rating = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    product_price = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    product_stock_count = models.IntegerField(null=True, blank=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    _id = models.AutoField(primary_key=True, editable=False)
    number_of_reviews = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self):
        return self.product_name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address1 = models.CharField(max_length=255, null=True, blank=True)
    address2 = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.user.username


class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    _id = models.AutoField(primary_key=True, editable=False)
    was_bought = models.BooleanField(default=False)
    quantity = models.IntegerField()
    date_to_be_delivered = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} bought {self.product.product_name}"


logger = logging.getLogger(__name__)


class LogEntry(models.Model):
    LEVEL_CHOICES = [
        ("DEBUG", "Debug"),
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("CRITICAL", "Critical"),
    ]

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    message = models.TextField()
    module = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp} - {self.level} - {self.module} - {self.message}"
