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
        label="Username or Email",
        widget=forms.TextInput(attrs={'placeholder': 'Enter username or email'})
    )
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_username_or_email(self):
        username_or_email = self.cleaned_data.get('username_or_email')
        if '@' in username_or_email:
            try:
                CustomUser.objects.get(email=username_or_email)
            except CustomUser.DoesNotExist:
                raise ValidationError("No user found with this email address.")
        else:
            try:
                CustomUser.objects.get(username=username_or_email)
            except CustomUser.DoesNotExist:
                raise ValidationError("No user found with this username.")
        return username_or_email