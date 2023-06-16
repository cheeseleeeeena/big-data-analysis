from django.urls import path
from app_custom_keyword import views

app_name="app_custom_keyword"

urlpatterns = [
    
    # the first way:
    path('', views.home, name='home'),
    path('api_get_top_userkey/', views.api_get_top_userkey),
]
