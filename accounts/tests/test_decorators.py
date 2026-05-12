"""
TDD tests for admin_required decorator and AdminRequiredMixin.

High-risk area: authorization enforcement.
All acceptance criteria are required per roadmap Step 5.
Test-first: written before implementation.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.views import View

User = get_user_model()

ADMIN_LIST_URL = '/admin-portal/proposals/'
LOGIN_URL = '/admin-portal/login/'


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username='staff@example.com',
        email='staff@example.com',
        password='staffpass',
        is_staff=True,
        is_active=True,
    )


@pytest.fixture
def non_staff_user(db):
    return User.objects.create_user(
        username='nostaff@example.com',
        email='nostaff@example.com',
        password='notstaffpass',
        is_staff=False,
        is_active=True,
    )


# ============================================================
# Decorator tests via _stub_list URL (/admin-portal/proposals/)
# ============================================================

class TestAdminRequiredDecorator:

    def test_unauthenticated_redirects_to_login(self, client, db):
        response = client.get(ADMIN_LIST_URL)
        assert response.status_code == 302
        assert response['Location'].startswith(LOGIN_URL)

    def test_unauthenticated_redirect_includes_next_param(self, client, db):
        response = client.get(ADMIN_LIST_URL)
        assert 'next=' in response['Location']
        assert 'admin-portal/proposals' in response['Location']

    def test_non_staff_authenticated_returns_403(self, client, non_staff_user):
        client.force_login(non_staff_user)
        response = client.get(ADMIN_LIST_URL)
        assert response.status_code == 403

    def test_staff_authenticated_proceeds_to_view(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get(ADMIN_LIST_URL)
        assert response.status_code == 200


# ============================================================
# AdminRequiredMixin tests via RequestFactory
# ============================================================

class TestAdminRequiredMixin:

    def _make_mixin_view(self):
        from accounts.decorators import AdminRequiredMixin

        class _ProtectedView(AdminRequiredMixin, View):
            def get(self, request, *args, **kwargs):
                return HttpResponse('OK', status=200)

        return _ProtectedView.as_view()

    def test_unauthenticated_redirects_to_login(self):
        view = self._make_mixin_view()
        factory = RequestFactory()
        request = factory.get('/fake-admin/')
        request.user = AnonymousUser()
        response = view(request)
        assert response.status_code == 302
        assert '/admin-portal/login/' in response['Location']

    def test_unauthenticated_redirect_includes_next_param(self):
        view = self._make_mixin_view()
        factory = RequestFactory()
        request = factory.get('/fake-admin/')
        request.user = AnonymousUser()
        response = view(request)
        assert 'next=' in response['Location']

    def test_non_staff_raises_permission_denied(self, non_staff_user):
        view = self._make_mixin_view()
        factory = RequestFactory()
        request = factory.get('/fake-admin/')
        request.user = non_staff_user
        with pytest.raises(PermissionDenied):
            view(request)

    def test_staff_authenticated_proceeds_to_view(self, staff_user):
        view = self._make_mixin_view()
        factory = RequestFactory()
        request = factory.get('/fake-admin/')
        request.user = staff_user
        response = view(request)
        assert response.status_code == 200
