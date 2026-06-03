from django.shortcuts import render
import logging
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from axes.handlers.proxy import AxesProxyHandler
from .forms import LoginForm, UserRegistrationForm
from .models import User

audit = logging.getLogger('audit')

def login_view(request):
    # Check honeypot
    if request.method == 'POST' and request.POST.get('phonenumber'):
        audit.warning(f'HONEYPOT_TRIGGERED | ip={get_client_ip(request)} | ts={timezone.now()}')
        return render(request, 'accounts/login.html', {'form': LoginForm(), 'error': 'Invalid submission.'})

    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            audit.info(f'LOGIN_SUCCESS | user={user.username} | role={user.role} | ip={get_client_ip(request)} | ts={timezone.now()}')
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            audit.warning(f'LOGIN_FAIL | ip={get_client_ip(request)} | username={request.POST.get("username","?")} | ts={timezone.now()}')

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        audit.info(f'LOGOUT | user={request.user.username} | ip={get_client_ip(request)} | ts={timezone.now()}')
    logout(request)
    return redirect('login')

@login_required
def register_user(request):
    if not request.user.is_lgu_admin():
        messages.error(request, 'Access denied. LGU Admin only.')
        return redirect('dashboard')
    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        audit.info(f'USER_CREATED | created_by={request.user.username} | new_user={user.username} | role={user.role} | ts={timezone.now()}')
        messages.success(request, f'User {user.username} created successfully.')
        return redirect('user_list')
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def user_list(request):
    if not request.user.is_lgu_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    users = User.objects.all().order_by('role', 'username')
    return render(request, 'accounts/user_list.html', {'users': users})

def lockout_view(request, credentials=None, *args, **kwargs):
    audit.warning(f'ACCOUNT_LOCKED | ip={get_client_ip(request)} | ts={timezone.now()}')
    return render(request, 'accounts/lockout.html', status=403)

def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR', 'unknown')

# Create your views here.
