# poker_project/poker/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('add-coins/', views.add_coins, name='add_coins'),
]