from django.contrib.auth import login, authenticate, logout
from django.core.mail import send_mail
from apps.users.forms import CustomUserCreationForm, LoginForm
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .models import CustomUser
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

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
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('poker:initialize_game')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('users:login')

@login_required
@require_POST
def add_coins(request):
    try:
        user = request.user
        user.add_coins(1000)  # Using the model method
        return JsonResponse({
            'success': True,
            'new_balance': user.coins,
            'message': 'Successfully added 1000 coins!'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)