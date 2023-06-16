from django.urls import path
from app_pk import views

app_name='app_pk'

urlpatterns = [

    path('', views.home, name='home'),
    path('api_get_pk_data/', views.api_get_pk_data),

]
