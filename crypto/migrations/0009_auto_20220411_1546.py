# Generated by Django 3.2.9 on 2022-04-11 13:46

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0008_transcaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transcaction',
            name='created',
        ),
        migrations.AddField(
            model_name='transcaction',
            name='day_created',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transcaction',
            name='time_created',
            field=models.TimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
