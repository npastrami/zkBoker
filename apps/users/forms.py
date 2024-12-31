# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
import pytz

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

class UserSettingsForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        label='New Password'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        label='Confirm New Password'
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'profile_picture', 'location',
            'timezone', 'github_link', 'linkedin_link', 'website_link',
            'resume'
        ]
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'hidden-file-input'
            }),
            'resume': forms.FileInput(attrs={
                'accept': '.pdf,.doc,.docx',
                'class': 'hidden-file-input'
            }),
            'timezone': forms.Select(choices=[(tz, tz) for tz in pytz.all_timezones]),
            'location': forms.TextInput(attrs={'placeholder': 'City, Country'}),
            'github_link': forms.TextInput(attrs={'placeholder': 'Github profile'}),
            'linkedin_link': forms.TextInput(attrs={'placeholder': 'LinkedIn profile'}),
            'website_link': forms.TextInput(attrs={'placeholder': 'Personal website'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional except username and email
        for field in self.fields:
            if field not in ['username', 'email']:
                self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and not password2:
            raise forms.ValidationError("Please confirm your password")
        if password2 and not password1:
            raise forms.ValidationError("Please enter your password")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and CustomUser.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError('Email address is already in use.')
        return email
