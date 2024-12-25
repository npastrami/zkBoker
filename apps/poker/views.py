# poker/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import GameSession
from .game_manager import PokerGameManager
import json

@login_required
def initialize_game(request):
    """Initialize a new game session"""
    session = GameSession.objects.create()
    
    return render(request, 'poker/game.html', {
        'session_id': session.session_id,
        'player_stack': session.player_stack,
        'bot_stack': session.bot_stack,
        'pot': session.pot,
        'board_cards': [],
        'player_cards': [],
        'game_message': 'Click "Start New Hand" to begin playing!'
    })

def start_hand(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        session = GameSession.objects.get(session_id=data.get('session_id'))
        game_manager = PokerGameManager(session)
        
        response_data = game_manager.start_new_hand()
        return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def make_move(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        session = GameSession.objects.get(session_id=data.get('session_id'))
        game_manager = PokerGameManager(session)
        
        response_data = game_manager.process_player_action(
            data.get('action'),
            data.get('amount', 0)
        )
        
        return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def home_view(request):
    return render(request, 'poker/home.html')

@login_required
def staking_view(request):
    return render(request, 'poker/staking.html')