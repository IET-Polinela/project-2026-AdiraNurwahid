from django.urls import path
from .views import (
    login_view,
    register_view,
    logout_view,
    admin_panel,
    DashboardView,
    status_chart,
    category_chart
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

    # ✅ Dashboard pakai CBV
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    path('admin-panel/', admin_panel, name='admin_panel'),

    # ✅ API (WAJIB buat chart)
    path('api/status/', status_chart),
    path('api/category/', category_chart),
]