# Generated by Django 5.0.3 on 2024-06-05 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docesal_be', '0007_remove_product_product_was_bought'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='product_was_bought',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]