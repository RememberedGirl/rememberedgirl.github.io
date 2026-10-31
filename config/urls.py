from django.urls import path
from board import views

urlpatterns = [path('index.html', views.home), path('', views.home, name='home'), path('players/<slug:slug>/', views.player, name='player')]
