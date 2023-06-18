from django.urls import path
from django.urls import include

urlpatterns = [
    path('heho/', include('app_top_keyword_heho.urls')),
    path('ithome/', include('app_top_keyword_ithome.urls')),
    path('horoscope/', include('app_top_keyword_horoscope.urls')),
]