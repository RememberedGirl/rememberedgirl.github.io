from django.urls import path
from board import views

urlpatterns = [path('2PQQ2RJ0R/players/<slug:slug>/', views.other_player), path('2PQQ2RJ0R/', views.other_clan), path('2PQQ2RJ0R/index.html', views.other_clan), path('berserk/', views.home, {'design': 'berserk'}), path('berserk/index.html', views.home, {'design': 'berserk'}), path('berserk/players/<slug:slug>/', views.player, {'design': 'berserk'}), path('index.html', views.home), path('', views.home, name='home'), path('players/<slug:slug>/', views.player, name='player')]
