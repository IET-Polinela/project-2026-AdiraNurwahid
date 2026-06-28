from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Report
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from django.db.models import Q
from rest_framework import generics, permissions
from .serializers import ReportSerializer
from drf_spectacular.utils import extend_schema_view, extend_schema


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to restrict access to admin (is_staff) users only."""
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super(LoginRequiredMixin, self).handle_no_permission()
        return redirect('report_list')


@login_required
def about_view(request):
    return render(request, 'main_app/about.html')


@login_required
def contacts_view(request):
    return render(request, 'main_app/contacts.html')

# LIST - only admin
class ReportListView(AdminRequiredMixin, ListView):
    model = Report
    template_name = 'main_app/home.html'
    context_object_name = 'reports'

# DETAIL - only admin
class ReportDetailView(AdminRequiredMixin, DetailView):
    model = Report
    template_name = 'main_app/report_detail.html'

# CREATE - only admin
class ReportCreateView(AdminRequiredMixin, CreateView):
    model = Report
    fields = ['title', 'category', 'description', 'location']
    template_name = 'main_app/add_report.html'
    success_url = reverse_lazy('report_list')

# UPDATE - only admin
class ReportUpdateView(AdminRequiredMixin, UpdateView):
    model = Report
    fields = ['title', 'category', 'description', 'location', 'status']
    template_name = 'main_app/edit_report.html'
    success_url = reverse_lazy('report_list')

# DELETE - only admin
class ReportDeleteView(AdminRequiredMixin, DeleteView):
    model = Report
    template_name = 'main_app/delete_report.html'
    success_url = reverse_lazy('report_list')

# STATUS UPDATE - only admin
class ReportUpdateStatusView(AdminRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        report.status = request.POST.get('status')
        report.save()
        messages.success(request, "Status berhasil diubah!")
        return redirect('report_list')


def admin_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return HttpResponse("Akses Ditolak", status=403)
        if not request.user.is_staff:
            return HttpResponse("Akses Ditolak", status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# API untuk search reports - admin only
@admin_only
def search_reports(request):
    q = request.GET.get('q', '')
    reports = Report.objects.filter(
        Q(title__icontains=q) |
        Q(category__icontains=q) |
        Q(location__icontains=q)
    )[:20]
    data = list(reports.values('id', 'title', 'category', 'location', 'status'))
    return JsonResponse(data, safe=False)


# API untuk detail report
@login_required
def report_detail(request, id):
    try:
        report = Report.objects.get(id=id)
        data = {
            "title": report.title,
            "category": report.category,
            "description": report.description,
            "location": report.location,
            "status": report.status,
        }
        return JsonResponse(data)
    except Report.DoesNotExist:
        return JsonResponse({'error': 'Report not found'}, status=404)

    # =========================
# DJANGO REST FRAMEWORK API
# =========================

class ReportListAPI(generics.ListCreateAPIView):

    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        # tampilkan:
        # - semua NON-DRAFT
        # - DRAFT milik sendiri

        return Report.objects.filter(
            Q(status__in=['REPORTED', 'VERIFIED']) |
            Q(status='DRAFT', reporter=self.request.user)
        )

    def perform_create(self, serializer):

        serializer.save(reporter=self.request.user)


@extend_schema_view(
    destroy=extend_schema(exclude=True)
)
class ReportDetailAPI(generics.RetrieveUpdateDestroyAPIView):

    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_destroy(self, instance):

        # hanya owner + status DRAFT
        if (
            instance.reporter != self.request.user or
            instance.status != 'DRAFT'
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Hanya pemilik laporan dengan status DRAFT yang dapat menghapus laporan."
            )

        instance.delete()

    def perform_update(self, serializer):

        instance = self.get_object()

        # hanya owner + DRAFT
        if (
            instance.reporter != self.request.user or
            instance.status != 'DRAFT'
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Hanya pemilik laporan dengan status DRAFT yang dapat mengubah laporan."
            )

        serializer.save()


@login_required
def report_detail_api(request, id):
    try:
        report = Report.objects.get(id=id)

        return JsonResponse({
            'id': report.id,
            'title': report.title,
            'category': report.category,
            'description': report.description,
            'location': report.location,
            'status': report.status,
        })

    except Report.DoesNotExist:
        raise Http404("Report not found")