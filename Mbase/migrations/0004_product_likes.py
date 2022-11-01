# Generated by Django 4.0.3 on 2022-09-21 10:03

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Mbase', '0003_rename_image_product_thumbnail_imagealbum'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='likes',
            field=models.ManyToManyField(blank=True, default=None, related_name='likes', to=settings.AUTH_USER_MODEL),
        ),
    ]
