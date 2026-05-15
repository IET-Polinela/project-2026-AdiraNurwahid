from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('main_app.urls')),
    path('auth/', include('usermanagement_24782002.urls')),

    path('dashboard/', include('dashboard_24782002.urls')),

    # API REST
    path('api/', include('main_app.api_urls')),
]