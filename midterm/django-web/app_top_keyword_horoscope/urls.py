from django.urls import path
from app_top_keyword_horoscope import views

app_name = "app_top_keyword_horoscope"

urlpatterns = [
    path('', views.home, name='home'),
    path('api_get_topword/', views.api_get_topword),
]
