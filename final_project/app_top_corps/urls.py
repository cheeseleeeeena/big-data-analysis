from django.urls import path
from . import views

app_name = "app_top_corps"

urlpatterns = [
    # top (popular) persons
    path('', views.home, name='home'),

    # ajax path
    path('api_get_topCorps/', views.api_get_topCorps),
]
