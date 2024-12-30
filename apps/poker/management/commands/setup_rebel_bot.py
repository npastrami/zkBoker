# poker/management/commands/setup_rebel_bot.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.poker.models import BotRepository, AvailableGame
import os

User = get_user_model()

REBEL_CODE = '''
# ReBeL bot implementation
from poker.rebel.player import ReBeL

class ReBeL_test(ReBeL):
    def __init__(self):
        super().__init__()
        self.name = "ReBeL_test"
'''

class Command(BaseCommand):
    help = 'Sets up the default ReBeL bot and creates an available game'

    def handle(self, *args, **kwargs):
        # Create or get admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'coins': 1000000,  # 1M coins for admin
                'email': 'admin@example.com'
            }
        )
        
        if created:
            admin_user.set_password('admin_password')  # Set a default password
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Create ReBeL bot in repository
        rebel_bot, created = BotRepository.objects.get_or_create(
            user=admin_user,
            name='ReBeL_test',
            defaults={
                'code': REBEL_CODE,
                'description': 'Default ReBeL test bot',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Created ReBeL bot in repository'))

        # Create available game for ReBeL
        game, created = AvailableGame.objects.get_or_create(
            user=admin_user,
            bot=rebel_bot,
            defaults={
                'bot_name': 'ReBeL_test',
                'game_type': 'coins',
                'total_hands': 100000,
                'remaining_hands': 100000,
                'initial_stack': 400,
                'max_rebuys': 250,  # Allow for long sessions
                'is_active': True
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('Created default ReBeL available game')
            )
        else:
            # Update existing game
            game.remaining_hands = 100000
            game.is_active = True
            game.save()
            self.stdout.write(
                self.style.SUCCESS('Updated existing ReBeL game')
            )