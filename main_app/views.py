from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Report
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

# LIST + SEARCH
class ReportListView(ListView):
    model = Report
    template_name = 'home.html'
    context_object_name = 'reports'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Report.objects.filter(title__icontains=query)
        return Report.objects.all()

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

    def form_valid(self, form):
        messages.success(self.request, "Laporan berhasil ditambahkan!")
        return super().form_valid(form)

# UPDATE
class ReportUpdateView(UpdateView):
    model = Report
    fields = ['title', 'category', 'description', 'location']
    template_name = 'edit_report.html'
    success_url = reverse_lazy('report_list')

    def form_valid(self, form):
        messages.success(self.request, "Laporan berhasil diupdate!")
        return super().form_valid(form)

# DELETE
class ReportDeleteView(DeleteView):
    model = Report
    template_name = 'delete_report.html'
    success_url = reverse_lazy('report_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Laporan berhasil dihapus!")
        return super().delete(request, *args, **kwargs)

# WORKFLOW STATUS
class ReportUpdateStatusView(View):
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        new_status = request.POST.get('status')

        if new_status:
            report.status = new_status
            report.save()
            messages.success(request, "Status berhasil diubah!")

        return redirect('report_list')