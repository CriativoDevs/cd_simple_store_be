from django.db import models
from django.contrib.auth.models import User


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
