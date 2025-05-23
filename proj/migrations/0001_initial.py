# Generated by Django 5.2 on 2025-04-30 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField()),
                ('condition', models.TextField()),
                ('made_year', models.IntegerField()),
                ('kilometers', models.IntegerField()),
                ('engine_size', models.IntegerField()),
                ('location', models.TextField()),
                ('seller_name', models.TextField()),
                ('product_image', models.ImageField(upload_to='product')),
            ],
        ),
    ]
