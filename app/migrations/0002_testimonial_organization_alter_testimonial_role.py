# Generated by Django 5.2.1 on 2025-06-04 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='testimonial',
            name='organization',
            field=models.CharField(default='none', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='testimonial',
            name='role',
            field=models.CharField(max_length=255),
        ),
    ]
