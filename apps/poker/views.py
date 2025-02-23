# poker/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import GameSession, AvailableGame, BotRepository
from .game_manager import PokerGameManager
import json
from .forms import JoinGameForm, CreateGameForm
from django.conf import settings
from apps.users.models import CustomUser
from django.views.decorators.http import require_POST
import subprocess
import tempfile
import os

@login_required
def game_table(request):
    """View for displaying available games"""
    available_games = AvailableGame.objects.filter(
        is_active=True,
        remaining_hands__gt=0
    ).select_related('user', 'bot')
    
    return render(request, 'poker/game_table.html', {
        'available_games': available_games,
        'join_form': JoinGameForm(),
        'create_form': CreateGameForm()
    })

@login_required
@require_POST
def join_game(request):
    """Handle joining an available game"""
    try:
        data = json.loads(request.body)
        form = JoinGameForm(data)
        
        if form.is_valid():
            game_id = form.cleaned_data['game_id']
            play_mode = form.cleaned_data['play_mode']
            num_hands = form.cleaned_data['num_hands']
            initial_stack = form.cleaned_data['initial_stack']
            max_rebuys = form.cleaned_data['max_rebuys']
            player_bot_id = form.cleaned_data.get('player_bot_id')
            
            # Get the available game
            available_game = AvailableGame.objects.get(id=game_id, is_active=True)
            
            # Get player bot if in bot mode
            player_bot = None
            if play_mode == 'bot' and player_bot_id:
                player_bot = BotRepository.objects.get(id=player_bot_id, user=request.user)
            
            # Create new game session
            session = GameSession.objects.create(
                player=request.user,
                play_mode=play_mode,
                player_bot=player_bot,
                opponent_bot=available_game.bot,
                player_stack=initial_stack,
                bot_stack=available_game.initial_stack,
                available_game=available_game,
                hands_to_play=min(num_hands, available_game.remaining_hands),
                player_initial_stack=initial_stack,
                player_max_rebuys=max_rebuys
            )
            
            # Update available game's remaining hands
            available_game.remaining_hands -= num_hands
            if available_game.remaining_hands <= 0:
                available_game.is_active = False
            available_game.save()
            
            return JsonResponse({
                'success': True,
                'redirect_url': f'/game/initialize/?session_id={session.session_id}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid form data',
                'errors': form.errors
            })
            
    except AvailableGame.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Game no longer available'
        })
    except BotRepository.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Selected bot not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def post_bot(request):
    """Handle posting a new bot for other players"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            total_hands = int(data.get('total_hands', 0))
            game_type = data.get('game_type')
            initial_stack = int(data.get('initial_stack', 0))
            max_rebuys = int(data.get('max_rebuys', 0))
            bot_code = data.get('bot_code')
            
            # Validate inputs
            if not all([total_hands, game_type, initial_stack, bot_code]):
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required fields'
                })
                
            if not (100 <= total_hands <= 10000):
                return JsonResponse({
                    'success': False,
                    'message': 'Total hands must be between 100 and 10,000'
                })
                
            # Create new available game
            AvailableGame.objects.create(
                user=request.user,
                game_type=game_type,
                total_hands=total_hands,
                remaining_hands=total_hands,
                initial_stack=initial_stack,
                max_rebuys=max_rebuys,
                bot_code=bot_code
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Bot posted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
def initialize_game(request):
    """Initialize a game session after selecting a game"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('poker:game')
        
    try:
        session = GameSession.objects.get(
            session_id=session_id,
            player=request.user
        )
        
        # Prepare game state based on play mode
        if session.play_mode == 'human':
            return render(request, 'poker/game.html', {
                'session_id': session.session_id,
                'player_stack': session.player_stack,
                'bot_stack': session.bot_stack,
                'pot': session.pot,
                'board_cards': [],
                'player_cards': [],
                'game_message': 'Click "Start New Hand" to begin playing!',
                'user': request.user,
                'hands_to_play': session.hands_to_play,
                'hands_played': session.hands_played
            })
        else:
            # Handle bot vs bot mode
            # TODO: Implement bot vs bot gameplay
            return render(request, 'poker/bot_game.html', {
                'session_id': session.session_id,
                'player_bot': session.player_bot.name,
                'opponent_bot': session.opponent_bot.name,
                'hands_to_play': session.hands_to_play,
                'hands_played': session.hands_played
            })
            
    except GameSession.DoesNotExist:
        return redirect('poker:game')
    
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
    context = {
        'title': 'Development Environment',
        'disable_navigation': True  # This will help with fullscreen mode
    }
    return render(request, 'poker/dev.html', context)

@login_required
@require_POST
def save_code(request):
    try:
        data = json.loads(request.body)
        code = data.get('code')
        language = data.get('language')
        file_path = data.get('file_path')
        
        if not all([code, language, file_path]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            })

        # Update path to match your project structure
        full_path = os.path.join(settings.BASE_DIR, 'apps', 'poker', 'skeletons', file_path)
        
        # Security check with updated path
        if not os.path.abspath(full_path).startswith(
            os.path.abspath(os.path.join(settings.BASE_DIR, 'apps', 'poker', 'skeletons'))
        ):
            raise ValueError("Invalid file path")
            
        with open(full_path, 'w') as f:
            f.write(code)
            
        return JsonResponse({
            'success': True,
            'message': 'Code saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
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
        # Clean the path
        clean_path = os.path.normpath(path)
        file_path = os.path.join(settings.BASE_DIR, 'apps', 'poker', 'skeletons', clean_path)
        
        print(f"Attempting to read file: {file_path}")  # Debug print
        
        # Security check
        skeleton_base = os.path.abspath(os.path.join(settings.BASE_DIR, 'apps', 'poker', 'skeletons'))
        if not os.path.abspath(file_path).startswith(skeleton_base):
            raise ValueError("Invalid file path")
        
        if not os.path.isfile(file_path):
            raise ValueError(f"Not a file: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"Successfully read file, content length: {len(content)}")  # Debug print
            
        # Determine language based on extension
        extension = os.path.splitext(path)[1].lower()
        language = {
            '.py': 'python',
            '.cpp': 'cpp',
            '.h': 'cpp',
            '.json': 'json'
        }.get(extension, 'text')
            
        return JsonResponse({
            'success': True,
            'content': content,
            'language': language
        })
    except Exception as e:
        print(f"Error reading file: {str(e)}")  # Debug print
        return JsonResponse({
            'success': False,
            'error': str(e)
        })