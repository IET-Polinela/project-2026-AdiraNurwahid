from django.urls import path
from .views import login_view, register_view, logout_view, dashboard_view, admin_panel

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('admin-panel/', admin_panel, name='admin_panel'),
]