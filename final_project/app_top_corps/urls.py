from django.urls import path
from app_top_corps import views

app_name="app_top_corps"

urlpatterns = [
    # top (popular) persons
    path('', views.home, name='home'),

    # ajax path
    path('api_get_topPerson/', views.api_get_topPerson),
]
