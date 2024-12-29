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
    path('dev/', views.staking_view, name='dev'),
    path('buy_in/', views.buy_in, name='buy_in'),
    path('exit_game/', views.exit_game, name='exit_game'),
    path('dev/save-code/', views.save_code, name='save_code'),
    path('dev/run-code/', views.run_code, name='run_code'),
    path('dev/skeletons/', views.get_skeleton_files, name='get_skeleton_files'),
    path('dev/skeletons/<path:path>', views.get_skeleton_file_content, name='get_skeleton_file_content'),
]