# poker_project/poker/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
app_name = 'poker'


urlpatterns = [
    path('', views.initialize_game, name='initialize_game'),
    path('make_move/', views.make_move, name='make_move'),
    path('start_hand/', views.start_hand, name='start_hand'),
    
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='poker:login'), name='logout'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
]