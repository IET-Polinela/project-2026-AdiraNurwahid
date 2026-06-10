from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from django.http import JsonResponse
from django.db.models import Count

from main_app.models import Report

User = get_user_model()


# ================= AUTH =================

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username atau password salah!')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if not username or not password or not email:
            messages.error(request, 'Semua field wajib diisi!')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan!')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email sudah digunakan!')
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.role = role

        if role == 'admin':
            user.is_staff = True

        user.save()

        messages.success(request, 'Akun berhasil dibuat!')
        return redirect('login')

    return render(request, 'register.html')


# ================= DASHBOARD (CBV) =================

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


# ================= API (WAJIB TUGAS) =================

def status_chart(request):
    data = Report.objects.values('status').annotate(total=Count('id'))

    return JsonResponse({
        'labels': [x['status'] for x in data],
        'data': [x['total'] for x in data]
    })


def category_chart(request):
    data = Report.objects.values('category').annotate(total=Count('id'))

    return JsonResponse({
        'labels': [x['category'] for x in data],
        'data': [x['total'] for x in data]
    })


# ================= ADMIN =================

def admin_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.is_staff or request.user.role == 'admin'):
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_only
def admin_panel(request):
    return render(request, 'admin_panel.html')