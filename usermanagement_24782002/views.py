from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required

User = get_user_model()


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


@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')

from django.http import HttpResponse

# middleware sederhana untuk admin
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