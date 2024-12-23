# poker_project/poker/urls.py
from django.urls import path
from . import views

app_name = 'poker'


urlpatterns = [
    path('', views.initialize_game, name='initialize_game'),
    path('make_move/', views.make_move, name='make_move'),
    path('start_hand/', views.start_hand, name='start_hand'),
]