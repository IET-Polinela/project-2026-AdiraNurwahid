from django.urls import path
from .views import *

urlpatterns = [
    path('', ReportListView.as_view(), name='report_list'),
    path('add/', ReportCreateView.as_view(), name='add_report'),
    path('detail/<int:pk>/', ReportDetailView.as_view(), name='detail_report'),
    path('edit/<int:pk>/', ReportUpdateView.as_view(), name='edit_report'),
    path('delete/<int:pk>/', ReportDeleteView.as_view(), name='delete_report'),
    path('update-status/<int:pk>/', ReportUpdateStatusView.as_view(), name='update_status'),
    path('about/', about_view, name='about'),
    path('contacts/', contacts_view, name='contacts'),
    # API endpoints are registered in main_app.api_urls and included from project urls.py
]