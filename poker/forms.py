# poker/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label='Email or username',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Email or username'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

    def clean_username_or_email(self):
        email = self.cleaned_data.get('email')
        
        try:
            CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise ValidationError("No user found with this email address.")
        return email