from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from usermanagement_24782002.api_views import RegisterView

urlpatterns = [
    # Homepage → langsung ke halaman laporan
    path('', RedirectView.as_view(url='/laporan/', permanent=False)),

    # Django Admin
    path('admin/', admin.site.urls),

    # Web Views
    path('laporan/', include('main_app.urls')),
    path('auth/dashboard/', include('dashboard_24782002.urls')),
    path('auth/', include('usermanagement_24782002.urls')),

    # API
    path('api/', include('main_app.api_urls')),

    # JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Register
    path('api/auth/register/', RegisterView.as_view(), name='api_register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)