# poker_project/poker/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'poker'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('make_move/', views.make_move, name='make_move'),
    path('start_hand/', views.start_hand, name='start_hand'),
    path('game/', views.initialize_game, name='game'),
    path('staking/', views.staking_view, name='staking'),
    path('buy_in/', views.buy_in, name='buy_in'),
    path('exit_game/', views.exit_game, name='exit_game'),
]