from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Report
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from rest_framework import generics, permissions
from .serializers import ReportSerializer



@login_required
def about_view(request):
    return render(request, 'about.html')


@login_required
def contacts_view(request):
    return render(request, 'contacts.html')

# LIST
class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'home.html'
    context_object_name = 'reports'

# DETAIL
class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'report_detail.html'

# CREATE
class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    fields = ['title', 'category', 'description', 'location']
    template_name = 'add_report.html'
    success_url = reverse_lazy('report_list')

# UPDATE
class ReportUpdateView(LoginRequiredMixin, UpdateView):
    model = Report
    fields = ['title', 'category', 'description', 'location', 'status']
    template_name = 'edit_report.html'
    success_url = reverse_lazy('report_list')

# DELETE
class ReportDeleteView(LoginRequiredMixin, DeleteView):
    model = Report
    template_name = 'delete_report.html'
    success_url = reverse_lazy('report_list')

# STATUS
class ReportUpdateStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        report.status = request.POST.get('status')
        report.save()
        messages.success(request, "Status berhasil diubah!")
        return redirect('report_list')

def admin_only(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'admin':
            return HttpResponse("Akses Ditolak", status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

# API untuk search reports
@login_required
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