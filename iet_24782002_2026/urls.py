from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from usermanagement_24782002.api_views import RegisterView

urlpatterns = [
    path('admin/', admin.site.urls),

    # ========================
    # Web Views (Template)
    # ========================
    path('', include('main_app.urls')),
    path('auth/', include('usermanagement_24782002.urls')),
   # path('dashboard/', include('dashboard_24782002.urls')),

    # ========================
    # API REST (Lab 10)
    # ========================
    path('api/', include('main_app.api_urls')),

    # JWT Token Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Register Citizen
    path('api/auth/register/', RegisterView.as_view(), name='api_register'),
]
