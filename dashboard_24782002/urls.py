from django.urls import path
from .views import (
    DashboardView, chart_data, api_status, api_category,
    search_reports, report_detail
)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard_main'),
    path('data/', chart_data),
    path('api/status/', api_status, name='api_status'),
    path('api/category/', api_category, name='api_category'),
    path('api/search/', search_reports, name='search_reports'),
    path('api/report/<int:id>/', report_detail, name='report_detail'),
]