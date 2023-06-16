from django.urls import path
from django.urls import include

urlpatterns = [
    path('top-kw/', include('app_top_keyword.urls')),
    path('top-org/', include('app_top_organization.urls')),
    path('user-kw/', include('app_user_keyword.urls')),
    path('top-3c/', include('app_top_3c.urls')),
]
