from django.contrib.auth import login, authenticate, logout
from django.core.mail import send_mail
from apps.users.forms import CustomUserCreationForm, LoginForm, UserSettingsForm
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .models import CustomUser
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages


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
            
            try:
                user = CustomUser.objects.get(username=username)
                if user.password_change_pending:
                    messages.error(request, 'Please verify your password change via email before logging in.')
                    return render(request, 'registration/login.html', {'form': form})
            except CustomUser.DoesNotExist:
                pass
                
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('poker:game')
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
        
@login_required
def user_settings(request):
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # If password change is requested
            password1 = form.cleaned_data.get('password1')
            password2 = form.cleaned_data.get('password2')
            
            if password1 and password2 and password1 == password2:
                # Generate verification token
                verification_token = str(uuid.uuid4())
                user = request.user
                
                # Store the new password hash and token
                user.password_change_token = verification_token
                user.password_change_pending = True
                user.new_password_hash = make_password(password1)
                user.save()
                
                # Send verification email
                verification_link = f"{request.scheme}://{request.get_host()}/verify-password/{verification_token}"
                send_mail(
                    'Verify Password Change',
                    f'Click this link to verify your password change: {verification_link}\n\n'
                    f'If you did not request this change, please ignore this email and your password will remain unchanged.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                # Log the user out
                logout(request)
                messages.success(request, 'Please check your email to verify your password change.')
                return redirect('users:login')
            else:
                # Handle non-password updates
                form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('users:settings')
    else:
        form = UserSettingsForm(instance=request.user)
    
    return render(request, 'users/settings.html', {'form': form})

def verify_password_change(request, token):
    try:
        user = CustomUser.objects.get(password_change_token=token, password_change_pending=True)
        
        # Apply the new password
        user.password = user.new_password_hash
        user.password_change_token = ''
        user.password_change_pending = False
        user.new_password_hash = ''
        user.save()
        
        messages.success(request, 'Your password has been successfully changed. You can now login with your new password.')
        return redirect('users:login')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid or expired password change verification link.')
        return redirect('users:login')
