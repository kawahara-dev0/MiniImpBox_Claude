from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator

from .models import AdminLoginLog


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class AdminLoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('proposals_admin:list')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)
        success = user is not None

        AdminLoginLog.objects.create(
            email=email,
            success=success,
            ip_address=_get_client_ip(request),
        )

        if success:
            login(request, user)
            return redirect('proposals_admin:list')

        return render(request, self.template_name, {
            'error': 'Invalid email address or password.',
        })


@method_decorator(require_POST, name='dispatch')
class AdminLogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('accounts:login')
