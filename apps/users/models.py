from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    coins = models.IntegerField(default=0)  
    gems = models.IntegerField(default=0)
    
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

    def add_gems(self, amount):
        if amount < 0:
            raise ValueError("Cannot add negative gems")
        self.gems += amount
        self.save()

    def remove_gems(self, amount):
        if amount < 0:
            raise ValueError("Cannot remove negative gems")
        if self.gems < amount:
            raise ValueError("Not enough gems")
        self.gems -= amount
        self.save()

    def __str__(self):
        return self.username  # Changed from email to username