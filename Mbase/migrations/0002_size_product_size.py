# Generated by Django 4.0.3 on 2024-09-13 03:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Mbase', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Size',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='size',
            field=models.ManyToManyField(to='Mbase.size'),
        ),
    ]
