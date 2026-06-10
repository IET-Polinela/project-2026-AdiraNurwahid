from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db import models
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from main_app.models import Report


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_reported'] = Report.objects.filter(
            status='REPORTED'
        ).order_by('-created_at')[:5]
        context['latest_resolved'] = Report.objects.filter(
            status='RESOLVED'
        ).order_by('-created_at')[:5]
        return context


@login_required
def chart_data(request):
    status = Report.objects.values('status').annotate(count=Count('id'))
    category = Report.objects.values('category').annotate(count=Count('id'))

    return JsonResponse({
        'status': list(status),
        'category': list(category),
    })


@login_required
def api_status(request):
    """API endpoint untuk distribusi status report"""
    status_data = Report.objects.values('status').annotate(count=Count('id'))
    
    # Format response untuk Chart.js
    labels = [item['status'] for item in status_data if item['status']]
    data = [item['count'] for item in status_data if item['status']]
    
    return JsonResponse({'labels': labels, 'data': data})


@login_required
def api_category(request):
    """API endpoint untuk distribusi kategori report"""
    category_data = Report.objects.values('category').annotate(count=Count('id'))
    
    # Format response untuk Chart.js
    labels = [item['category'] for item in category_data if item['category']]
    data = [item['count'] for item in category_data if item['category']]
    
    return JsonResponse({'labels': labels, 'data': data})


@login_required
def search_reports(request):
    """API endpoint untuk pencarian laporan"""
    q = request.GET.get('q', '')
    
    # Filter berdasarkan title, category, atau location
    reports = Report.objects.filter(
        models.Q(title__icontains=q) |
        models.Q(category__icontains=q) |
        models.Q(location__icontains=q)
    )[:20]
    
    data = list(reports.values('id', 'title', 'category', 'location', 'status'))
    return JsonResponse(data, safe=False)


@login_required
def report_detail(request, id):
    """API endpoint untuk detail laporan"""
    try:
        r = Report.objects.get(id=id)
        return JsonResponse({
            'title': r.title,
            'category': r.category,
            'description': r.description,
            'location': r.location,
            'status': r.status,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Report.DoesNotExist:
        return JsonResponse({'error': 'Report not found'}, status=404)