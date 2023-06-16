from django.urls import path
from django.urls import include

urlpatterns = [
    # top keywords
    path('topwords/', include('app_top_keywords.urls')),
    path('topcorps/', include('app_top_corps.urls')),
    path('customkey/', include('app_custom_keyword.urls')),
    path('pk/', include('app_pk.urls')),
]