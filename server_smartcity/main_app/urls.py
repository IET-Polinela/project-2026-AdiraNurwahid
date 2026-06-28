from django.urls import path
from .views import *

urlpatterns = [
    path('', ReportListView.as_view(), name='report_list'),

    # Alias 'home' untuk kompatibilitas test
    path('home/', ReportListView.as_view(), name='home'),

    path('search/', search_reports, name='report_search'),

    path('add/', ReportCreateView.as_view(), name='add_report'),

    path(
        'detail/<int:pk>/',
        ReportDetailView.as_view(),
        name='report_detail'
    ),

    path(
        'edit/<int:pk>/',
        ReportUpdateView.as_view(),
        name='edit_report'
    ),

    # Alias update_report untuk kompatibilitas test
    path(
        'update/<int:pk>/',
        ReportUpdateView.as_view(),
        name='update_report'
    ),

    path(
        'delete/<int:pk>/',
        ReportDeleteView.as_view(),
        name='delete_report'
    ),

    path(
        'update-status/<int:pk>/',
        ReportUpdateStatusView.as_view(),
        name='update_status'
    ),

    path('about/', about_view, name='about'),
    path('contacts/', contacts_view, name='contacts'),
]
