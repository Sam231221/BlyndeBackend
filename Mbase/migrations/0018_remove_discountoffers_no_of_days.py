# Generated by Django 4.0.3 on 2024-08-14 15:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Mbase', '0017_alter_discountoffers_end_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='discountoffers',
            name='no_of_days',
        ),
    ]
