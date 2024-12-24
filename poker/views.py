# poker/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.http import JsonResponse
from .models import GameSession, CustomUser
from .game_manager import PokerGameManager
from .forms import CustomUserCreationForm, LoginForm
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
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # Set to False if email verification required
            user.verification_token = str(uuid.uuid4())
            user.save()
            
            # Send verification email
            verification_link = f"{request.scheme}://{request.get_host()}/verify/{user.verification_token}"
            send_mail(
                'Verify your email',
                f'Click this link to verify your email: {verification_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return render(request, 'registration/signup_successful.html')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def verify_email(request, token):
    try:
        user = CustomUser.objects.get(verification_token=token)
        user.email_verified = True
        user.verification_token = ''
        user.save()
        return render(request, 'registration/verification_successful.html')
    except CustomUser.DoesNotExist:
        return render(request, 'registration/verification_failed.html')

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']
            
            # Determine if input is email or username
            if '@' in username_or_email:
                kwargs = {'email': username_or_email}
            else:
                kwargs = {'username': username_or_email}
            
            try:
                user = CustomUser.objects.get(**kwargs)
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('poker:initialize_game')
                else:
                    form.add_error('password', 'Invalid password')
            except CustomUser.DoesNotExist:
                form.add_error('username_or_email', 'User not found')
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')