# Generated by Django 5.1.3 on 2025-05-06 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proj', '0006_sellerinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='bluebook_page2',
            field=models.ImageField(blank=True, null=True, upload_to='bluebook'),
        ),
        migrations.AddField(
            model_name='product',
            name='bluebook_page9',
            field=models.ImageField(blank=True, null=True, upload_to='bluebook'),
        ),
    ]
