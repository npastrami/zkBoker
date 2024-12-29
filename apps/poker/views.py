# poker/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import GameSession
from .game_manager import PokerGameManager
import json
from django.conf import settings
from apps.users.models import CustomUser
from django.views.decorators.http import require_POST
import subprocess
import tempfile
import os

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
    return render(request, 'poker/dev.html')

@login_required
@require_POST
def save_code(request):
    data = json.loads(request.body)
    code = data.get('code')
    language = data.get('language')
    
    return JsonResponse({
        'success': True,
        'message': 'Code saved successfully'
    })

@login_required
@require_POST
def run_code(request):
    data = json.loads(request.body)
    code = data.get('code')
    language = data.get('language')
    
    with tempfile.NamedTemporaryFile(delete=False, 
                                    suffix='.py' if language == 'python' else '.cpp') as f:
        f.write(code.encode())
        temp_file = f.name
    
    try:
        if language == 'python':
            result = subprocess.run(['python', temp_file], 
                                    capture_output=True, 
                                    text=True, 
                                    timeout=5)
        else:  # C++
            # First compile
            compiled_file = temp_file[:-4]  # Remove .cpp
            compile_result = subprocess.run(['g++', temp_file, '-o', compiled_file], 
                                            capture_output=True, 
                                            text=True)
            
            if compile_result.returncode != 0:
                return JsonResponse({
                    'success': False,
                    'error': f'Compilation error:\n{compile_result.stderr}'
                })
            
            # Then run
            result = subprocess.run([compiled_file], 
                                    capture_output=True, 
                                    text=True, 
                                    timeout=5)
        
        output = result.stdout
        if result.stderr:
            output += f'\nErrors:\n{result.stderr}'
        
        return JsonResponse({
            'success': True,
            'output': output
        })
        
    finally:
        # Cleanup temporary files
        os.unlink(temp_file)
        if language == 'cpp' and os.path.exists(compiled_file):
            os.unlink(compiled_file)
            
@login_required
def get_skeleton_files(request):
    skeleton_path = os.path.join(settings.BASE_DIR, 'apps', 'poker', 'skeletons')
    print(f"Looking for skeletons in: {skeleton_path}")  # Debug print
    skeleton_structure = []
    
    try:
        # First check if path exists
        if not os.path.exists(skeleton_path):
            print(f"Skeleton path does not exist: {skeleton_path}")  # Debug print
            return JsonResponse({'success': False, 'error': 'Skeleton directory not found'})

        # Get all subdirectories
        for item in os.listdir(skeleton_path):
            item_path = os.path.join(skeleton_path, item)
            
            # Skip __pycache__ and hidden files
            if item.startswith('__') or item.startswith('.'):
                continue
                
            if os.path.isdir(item_path):
                folder = {
                    'name': item,
                    'type': 'directory',
                    'path': item,
                    'children': []
                }
                
                # Get files in this directory
                for file in os.listdir(item_path):
                    if file.startswith('__') or file.startswith('.'):
                        continue
                        
                    file_path = os.path.join(item, file)
                    folder['children'].append({
                        'name': file,
                        'type': 'file',
                        'path': file_path
                    })
                    
                skeleton_structure.append(folder)
        
        print(f"Found structure: {skeleton_structure}")  # Debug print
        return JsonResponse({'success': True, 'data': skeleton_structure})
        
    except Exception as e:
        print(f"Error in get_skeleton_files: {str(e)}")  # Debug print
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_skeleton_file_content(request, path):
    try:
        file_path = os.path.join(settings.BASE_DIR, 'poker', 'skeletons', path)
        # Ensure the file is within the skeletons directory
        if not os.path.abspath(file_path).startswith(
            os.path.abspath(os.path.join(settings.BASE_DIR, 'poker', 'skeletons'))
        ):
            raise ValueError("Invalid file path")
            
        with open(file_path, 'r') as f:
            content = f.read()
            
        return JsonResponse({
            'success': True,
            'content': content,
            'language': 'python' if path.endswith('.py') else 'text'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})