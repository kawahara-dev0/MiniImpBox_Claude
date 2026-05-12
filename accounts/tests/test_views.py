"""
Test-first tests for accounts views: AdminLoginView, AdminLogoutView.

High-risk area: authentication views + AdminLoginLog audit write.
All acceptance criteria are required per roadmap Step 4.
Test-first: written before implementation.
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import AdminLoginLog

User = get_user_model()

LOGIN_URL = '/admin-portal/login/'
LOGOUT_URL = '/admin-portal/logout/'
ADMIN_LIST_URL = '/admin-portal/proposals/'


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='admin@example.com',
        email='admin@example.com',
        password='correct-password',
        is_staff=True,
        is_active=True,
    )


@pytest.fixture
def non_staff_user(db):
    return User.objects.create_user(
        username='nostaff@example.com',
        email='nostaff@example.com',
        password='correct-password',
        is_staff=False,
        is_active=True,
    )


# ---------------------------------------------------------------------------
# AdminLoginView — GET
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminLoginViewGet:
    def test_get_renders_login_form(self, client):
        response = client.get(LOGIN_URL)
        assert response.status_code == 200

    def test_get_contains_email_and_password_fields(self, client):
        response = client.get(LOGIN_URL)
        content = response.content.decode()
        assert 'email' in content
        assert 'password' in content

    def test_get_contains_csrf_token(self, client):
        response = client.get(LOGIN_URL)
        content = response.content.decode()
        assert 'csrfmiddlewaretoken' in content

    def test_get_already_authenticated_staff_redirects_to_list(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(LOGIN_URL)
        assert response.status_code == 302
        assert response['Location'] == ADMIN_LIST_URL


# ---------------------------------------------------------------------------
# AdminLoginView — POST (correct credentials)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminLoginViewPostSuccess:
    def test_correct_credentials_redirects_to_list(self, client, admin_user):
        response = client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'correct-password',
        })
        assert response.status_code == 302
        assert response['Location'] == ADMIN_LIST_URL

    def test_correct_credentials_creates_session(self, client, admin_user):
        client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'correct-password',
        })
        assert '_auth_user_id' in client.session

    def test_correct_credentials_writes_login_log_success_true(self, client, admin_user):
        client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'correct-password',
        })
        log = AdminLoginLog.objects.get(email='admin@example.com')
        assert log.success is True

    def test_correct_credentials_login_log_has_no_password(self, client, admin_user):
        client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'correct-password',
        })
        log = AdminLoginLog.objects.get(email='admin@example.com')
        # Verify no password value appears in any stored field
        assert 'correct-password' not in str(log.email)
        assert 'correct-password' not in str(log.success)
        assert 'correct-password' not in str(log.ip_address or '')


# ---------------------------------------------------------------------------
# AdminLoginView — POST (wrong credentials)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminLoginViewPostFailure:
    def test_wrong_password_returns_200(self, client, admin_user):
        response = client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'wrong-password',
        })
        assert response.status_code == 200

    def test_wrong_password_no_session(self, client, admin_user):
        client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'wrong-password',
        })
        assert '_auth_user_id' not in client.session

    def test_wrong_password_shows_generic_error(self, client, admin_user):
        response = client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'wrong-password',
        })
        content = response.content.decode()
        assert 'Invalid email address or password.' in content

    def test_wrong_password_writes_login_log_success_false(self, client, admin_user):
        client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'wrong-password',
        })
        log = AdminLoginLog.objects.get(email='admin@example.com')
        assert log.success is False

    def test_nonexistent_email_returns_200(self, client, db):
        response = client.post(LOGIN_URL, {
            'email': 'nobody@example.com',
            'password': 'any-password',
        })
        assert response.status_code == 200

    def test_nonexistent_email_no_session(self, client, db):
        client.post(LOGIN_URL, {
            'email': 'nobody@example.com',
            'password': 'any-password',
        })
        assert '_auth_user_id' not in client.session

    def test_nonexistent_email_shows_same_generic_error(self, client, db):
        """Error must be identical to wrong-password case (FR-AUTH-05: no account existence hint)."""
        response = client.post(LOGIN_URL, {
            'email': 'nobody@example.com',
            'password': 'any-password',
        })
        content = response.content.decode()
        assert 'Invalid email address or password.' in content

    def test_nonexistent_email_writes_login_log_success_false(self, client, db):
        client.post(LOGIN_URL, {
            'email': 'nobody@example.com',
            'password': 'any-password',
        })
        log = AdminLoginLog.objects.get(email='nobody@example.com')
        assert log.success is False

    def test_login_log_written_before_response_on_failure(self, client, admin_user):
        """Log must exist after failed POST (written before response)."""
        client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'wrong-password',
        })
        assert AdminLoginLog.objects.filter(email='admin@example.com').exists()


# ---------------------------------------------------------------------------
# AdminLoginLog — password must never appear
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminLoginLogSensitiveData:
    def test_password_not_in_any_log_column_on_success(self, client, admin_user):
        client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'correct-password',
        })
        log = AdminLoginLog.objects.latest('attempted_at')
        assert 'correct-password' not in log.email
        assert 'correct-password' not in str(log.success)
        assert 'correct-password' not in str(log.ip_address or '')

    def test_password_not_in_any_log_column_on_failure(self, client, admin_user):
        client.post(LOGIN_URL, {
            'email': 'admin@example.com',
            'password': 'secret-pass',
        })
        log = AdminLoginLog.objects.latest('attempted_at')
        assert 'secret-pass' not in log.email
        assert 'secret-pass' not in str(log.success)
        assert 'secret-pass' not in str(log.ip_address or '')


# ---------------------------------------------------------------------------
# AdminLogoutView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminLogoutView:
    def test_post_logout_invalidates_session(self, client, admin_user):
        client.force_login(admin_user)
        assert '_auth_user_id' in client.session
        client.post(LOGOUT_URL)
        assert '_auth_user_id' not in client.session

    def test_post_logout_redirects_to_login(self, client, admin_user):
        client.force_login(admin_user)
        response = client.post(LOGOUT_URL)
        assert response.status_code == 302
        assert response['Location'] == LOGIN_URL

    def test_get_logout_returns_405(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(LOGOUT_URL)
        assert response.status_code == 405

    def test_post_logout_unauthenticated_redirects_to_login(self, client, db):
        """Unauthenticated logout POST should redirect gracefully."""
        response = client.post(LOGOUT_URL)
        assert response.status_code == 302
        assert response['Location'] == LOGIN_URL
