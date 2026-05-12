from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    """Require authenticated user with is_staff=True."""
    @wraps(view_func)
    @login_required(login_url='/admin-portal/login/')
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapped_view


class AdminRequiredMixin(AccessMixin):
    """Mixin for CBVs: redirect unauthenticated, 403 for authenticated non-staff."""
    login_url = '/admin-portal/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
