# Generated by Django 5.1.3 on 2024-12-25 19:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poker', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='gamesession',
            name='current_coins',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='gamesession',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='game_sessions', to=settings.AUTH_USER_MODEL),
        ),
    ]