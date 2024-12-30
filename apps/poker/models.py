# poker/models.py
from django.db import models
import uuid
from django.core.exceptions import ValidationError
from apps.users.models import CustomUser

class BotRepository(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bots')
    name = models.CharField(max_length=50)
    code = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'bot_repository'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_bot_name_per_user'
            )
        ]

    def clean(self):
        if not self.id:  # Only check on creation
            active_bots = BotRepository.objects.filter(
                user=self.user,
                is_active=True
            ).count()
            if active_bots >= 5:
                raise ValidationError("Users can only have 5 active bots at a time.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class AvailableGame(models.Model):
    GAME_TYPES = (
        ('coins', 'Coins'),
        ('gems', 'Gems'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    bot = models.ForeignKey(
        BotRepository, 
        on_delete=models.CASCADE, 
        related_name='games',
        null=True,  # Allow null for migration
        default=None  # Default to None for migration
    )
    bot_name = models.CharField(max_length=50, default='ReBeL_test')  # Default for migration
    game_type = models.CharField(max_length=5, choices=GAME_TYPES)
    total_hands = models.IntegerField()
    remaining_hands = models.IntegerField()
    posted_on = models.DateTimeField(auto_now_add=True)
    initial_stack = models.IntegerField()
    max_rebuys = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'available_games'
        ordering = ['-posted_on']

class GameSession(models.Model):
    PLAY_MODES = (
        ('human', 'Human vs Bot'),
        ('bot', 'Bot vs Bot'),
    )

    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    player = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    play_mode = models.CharField(max_length=5, choices=PLAY_MODES, default='human')
    player_bot = models.ForeignKey(
        BotRepository, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='player_sessions'
    )
    opponent_bot = models.ForeignKey(
        BotRepository,
        on_delete=models.SET_NULL,
        null=True,
        related_name='opponent_sessions'
    )
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
    available_game = models.ForeignKey(AvailableGame, on_delete=models.SET_NULL, null=True)
    hands_to_play = models.IntegerField(default=0)
    hands_played = models.IntegerField(default=0)
    player_initial_stack = models.IntegerField(default=0)
    player_max_rebuys = models.IntegerField(default=0)

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