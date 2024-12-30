# poker/management/commands/clear_available_games.py
from django.core.management.base import BaseCommand
from apps.poker.models import AvailableGame

class Command(BaseCommand):
    help = 'Clears all available games before major schema changes'

    def handle(self, *args, **kwargs):
        AvailableGame.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully cleared all available games'))