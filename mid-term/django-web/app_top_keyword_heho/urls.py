from django.urls import path
from app_top_keyword_heho import views

# Declare a namespace for this APP
app_name = 'app_top_keyword_heho'

urlpatterns = [
    # For home
    path('', views.home, name='home'),
    
    # For Ajax
    path('api_get_cate_topword/', views.api_get_cate_topword),
]