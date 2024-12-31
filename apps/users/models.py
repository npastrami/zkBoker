# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import pytz

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]
USER_LEVEL_CHOICES = [
    (0, 'Novice'),
    (1, 'Beginner'),
    (2, 'Intermediate'),
    (3, 'Advanced'),
    (4, 'Expert'),
    (5, 'Master')
]

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    coins = models.IntegerField(default=0)
    gems = models.IntegerField(default=0)
    total_gems_earned = models.BigIntegerField(default=0)
    user_level = models.IntegerField(choices=USER_LEVEL_CHOICES, default=0)
    
    # Profile fields
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    password_change_token = models.CharField(max_length=100, blank=True)
    password_change_pending = models.BooleanField(default=False)
    new_password_hash = models.CharField(max_length=128, blank=True)
    location = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='UTC')
    github_link = models.URLField(max_length=200, blank=True)
    linkedin_link = models.URLField(max_length=200, blank=True)
    website_link = models.URLField(max_length=200, blank=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)

    def update_level(self):
        """Update user level based on total gems earned"""
        for level in range(5, -1, -1):
            if self.total_gems_earned >= level * 1_000_000:
                if self.user_level != level:
                    self.user_level = level
                    self.save()
                return

    def add_gems(self, amount):
        if amount < 0:
            raise ValueError("Cannot add negative gems")
        self.gems += amount
        self.save()
        self.update_level()  # Update level after adding gems

    def remove_gems(self, amount):
        if amount < 0:
            raise ValueError("Cannot remove negative gems")
        if self.gems < amount:
            raise ValueError("Not enough gems")
        self.gems -= amount
        self.save()

    @property
    def progress(self):
        """Calculate progress to next level as percentage (0-100)"""
        if self.user_level >= 5:  # Max level reached
            return 100
            
        gems_for_current_level = self.user_level * 1_000_000
        gems_for_next_level = (self.user_level + 1) * 1_000_000
        gems_needed = gems_for_next_level - gems_for_current_level
        gems_progress = self.total_gems_earned - gems_for_current_level
        
        return min((gems_progress / gems_needed) * 100, 100)

    def add_coins(self, amount):
        if amount < 0:
            raise ValueError("Cannot add negative coins")
        self.coins += amount
        self.save()

    def remove_coins(self, amount):
        if amount < 0:
            raise ValueError("Cannot remove negative coins")
        if self.coins < amount:
            raise ValueError("Not enough coins")
        self.coins -= amount
        self.save()

    def __str__(self):
        return self.username