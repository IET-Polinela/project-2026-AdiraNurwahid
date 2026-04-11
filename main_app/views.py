from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Report
from django.views import View
from django.shortcuts import get_object_or_404, redirect

# LIST
class ReportListView(ListView):
    model = Report
    template_name = 'home.html'
    context_object_name = 'reports'

# DETAIL
class ReportDetailView(DetailView):
    model = Report
    template_name = 'report_detail.html'

# CREATE
class ReportCreateView(CreateView):
    model = Report
    fields = ['title', 'category', 'description', 'location']
    template_name = 'add_report.html'
    success_url = reverse_lazy('report_list')

# UPDATE
class ReportUpdateView(UpdateView):
    model = Report
    fields = ['title', 'category', 'description', 'location']
    template_name = 'edit_report.html'
    success_url = reverse_lazy('report_list')

# DELETE
class ReportDeleteView(DeleteView):
    model = Report
    template_name = 'delete_report.html'
    success_url = reverse_lazy('report_list')

# ✅ UPDATE STATUS (FIX ERROR)
class ReportUpdateStatusView(View):
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        report.status = 'VERIFIED'  # langsung isi
        report.save()
        return redirect('report_list')