# Generated by Django 5.0.3 on 2024-06-29 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docesal_be', '0011_delete_logentry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
