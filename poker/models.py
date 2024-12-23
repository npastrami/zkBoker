# poker/models.py
from django.db import models
import uuid
import json

class GameSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    player_stack = models.IntegerField(default=200)
    bot_stack = models.IntegerField(default=200)
    current_street = models.CharField(max_length=20)
    pot = models.IntegerField(default=0)
    player_cards = models.JSONField(default=list)
    board_cards = models.JSONField(default=list)
    deck_state = models.JSONField(default=dict)  # Store the deck state
    game_state = models.JSONField(default=dict)  # Store the current game state
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'game_sessions'