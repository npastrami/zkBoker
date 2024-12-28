# poker/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import GameSession
from .game_manager import PokerGameManager
import json
from apps.users.models import CustomUser

@login_required
def initialize_game(request):
    """Initialize a new game session"""
    # Get fresh user object to ensure we have the latest coin balance
    user = CustomUser.objects.get(id=request.user.id)
    session = GameSession.objects.create(player=user)
    
    return render(request, 'poker/game.html', {
        'session_id': session.session_id,
        'player_stack': session.player_stack,
        'bot_stack': session.bot_stack,
        'pot': session.pot,
        'board_cards': [],
        'player_cards': [],
        'game_message': 'Click "Start New Hand" to begin playing!',
        'user': user  # Pass the fresh user object to the template
    })

def start_hand(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        session = GameSession.objects.get(session_id=data.get('session_id'), player=request.user)
        game_manager = PokerGameManager(session)
        
        # Pass continue_session flag to start_new_hand
        continue_session = data.get('continue_session', False)
        response_data = game_manager.start_new_hand(continue_session)
        
        return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def make_move(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        session = GameSession.objects.get(session_id=data.get('session_id'), player=request.user)
        game_manager = PokerGameManager(session)
        
        response_data = game_manager.process_player_action(
            data.get('action'),
            data.get('amount', 0)
        )
        
        return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def buy_in(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    data = json.loads(request.body)
    session = GameSession.objects.get(
        session_id=data.get('session_id'),
        player=request.user
    )
    game_manager = PokerGameManager(session)
    success, message = game_manager.process_buy_in()
    
    if success:
        # Get the updated user object to ensure we have the latest coin balance
        user = CustomUser.objects.get(id=request.user.id)
        return JsonResponse({
            'success': True,
            'message': message,
            'updated_balance': user.coins  # This will have the new balance
        })
    else:
        return JsonResponse({
            'success': False,
            'message': message
        })

@login_required
def exit_game(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}) 
    data = json.loads(request.body)
    session = GameSession.objects.get(
        session_id=data.get('session_id'),
        player=request.user
    )
    # Create game manager with the correct player instance
    game_manager = PokerGameManager(session)
    
    # Process the exit and get remaining coins
    remaining_coins = game_manager.process_exit_game()
    
    # Get the updated coin balance
    updated_balance = request.user.coins
    return JsonResponse({
        'success': True,
        'message': f'Game exited successfully. {remaining_coins} coins returned to your account.',
        'coins_returned': remaining_coins,
        'current_coins': updated_balance
    })

@login_required
def home_view(request):
    return render(request, 'poker/home.html')

@login_required
def staking_view(request):
    return render(request, 'poker/staking.html')