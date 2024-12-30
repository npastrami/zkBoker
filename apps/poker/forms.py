# poker/forms.py
from django import forms
from .models import GameSession, AvailableGame

class JoinGameForm(forms.Form):
    game_id = forms.UUIDField()
    play_mode = forms.ChoiceField(
        choices=GameSession.PLAY_MODES,
        initial='human'
    )
    num_hands = forms.IntegerField(
        min_value=100,
        max_value=10000,
        required=True,
        widget=forms.NumberInput(attrs={'placeholder': 'Number of hands (100-10000)'})
    )
    initial_stack = forms.IntegerField(
        min_value=100,
        required=True,
        widget=forms.NumberInput(attrs={'placeholder': 'Initial stack size'})
    )
    max_rebuys = forms.IntegerField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={'placeholder': 'Maximum rebuys allowed'})
    )
    player_bot_id = forms.UUIDField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        play_mode = cleaned_data.get('play_mode')
        player_bot_id = cleaned_data.get('player_bot_id')

        if play_mode == 'bot' and not player_bot_id:
            raise forms.ValidationError('Bot selection is required for bot mode')

        return cleaned_data

class CreateGameForm(forms.ModelForm):
    class Meta:
        model = AvailableGame
        fields = ['bot', 'game_type', 'total_hands', 'initial_stack', 'max_rebuys']
        
    def clean_total_hands(self):
        total_hands = self.cleaned_data.get('total_hands')
        if total_hands < 100 or total_hands > 10000:
            raise forms.ValidationError('Total hands must be between 100 and 10,000')
        return total_hands

    def clean_initial_stack(self):
        initial_stack = self.cleaned_data.get('initial_stack')
        if initial_stack < 100:
            raise forms.ValidationError('Initial stack must be at least 100')
        return initial_stack