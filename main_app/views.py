from django.shortcuts import render, redirect
from .models import Report
from .forms import ReportForm

# CREATE
def add_report(request):
    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('report_list')
    else:
        form = ReportForm()
    return render(request, 'add_report.html', {'form': form})

# READ
def report_list(request):
    reports = Report.objects.all()
    return render(request, 'report_list.html', {'reports': reports})