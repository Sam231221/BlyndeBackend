# Generated by Django 4.0.3 on 2024-09-14 18:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Mbase', '0003_size_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='color',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='size',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
