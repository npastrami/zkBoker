# poker/models.py
from django.db import models
import uuid
from apps.users.models import CustomUser

class GameSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    player = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    player_stack = models.IntegerField(default=0)
    bot_stack = models.IntegerField(default=0)
    current_street = models.CharField(max_length=20)
    pot = models.IntegerField(default=0)
    player_cards = models.JSONField(default=list)
    board_cards = models.JSONField(default=list)
    deck_state = models.JSONField(default=dict)
    game_state = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    current_coins = models.IntegerField(default=0)

    class Meta:
        db_table = 'game_sessions'
        
class UserCode(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    code = models.TextField()
    language = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']