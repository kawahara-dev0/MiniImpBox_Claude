"""
Test-first tests for accounts.backends.EmailBackend.

High-risk area: authentication logic.
All test items are required per roadmap Step 3 acceptance criteria.
"""
import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model

from accounts.backends import EmailBackend

User = get_user_model()


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
def inactive_user(db):
    return User.objects.create_user(
        username='inactive@example.com',
        email='inactive@example.com',
        password='correct-password',
        is_staff=True,
        is_active=False,
    )


@pytest.mark.django_db
class TestEmailBackendAuthenticate:
    def test_correct_credentials_returns_user(self, admin_user):
        backend = EmailBackend()
        result = backend.authenticate(
            request=None,
            username='admin@example.com',
            password='correct-password',
        )
        assert result is not None
        assert result.pk == admin_user.pk

    def test_wrong_password_returns_none(self, admin_user):
        backend = EmailBackend()
        result = backend.authenticate(
            request=None,
            username='admin@example.com',
            password='wrong-password',
        )
        assert result is None

    def test_wrong_email_returns_none(self, db):
        backend = EmailBackend()
        result = backend.authenticate(
            request=None,
            username='nonexistent@example.com',
            password='any-password',
        )
        assert result is None

    def test_wrong_email_runs_dummy_hash_for_timing_mitigation(self, db):
        """Wrong-email path must call set_password to prevent timing-based account enumeration."""
        backend = EmailBackend()
        with patch.object(User, 'set_password') as mock_set_password:
            backend.authenticate(
                request=None,
                username='nonexistent@example.com',
                password='any-password',
            )
        mock_set_password.assert_called_once_with('any-password')

    def test_inactive_user_returns_none(self, inactive_user):
        """user_can_authenticate() must return False for inactive users."""
        backend = EmailBackend()
        result = backend.authenticate(
            request=None,
            username='inactive@example.com',
            password='correct-password',
        )
        assert result is None

    def test_empty_email_returns_none(self, db):
        backend = EmailBackend()
        result = backend.authenticate(
            request=None,
            username='',
            password='any-password',
        )
        assert result is None

    def test_none_username_returns_none(self, db):
        backend = EmailBackend()
        result = backend.authenticate(
            request=None,
            username=None,
            password='any-password',
        )
        assert result is None

    def test_authenticate_does_not_expose_existence_via_exception(self, db):
        """Wrong email path must not raise any exception (silent None return)."""
        backend = EmailBackend()
        try:
            result = backend.authenticate(
                request=None,
                username='doesnotexist@example.com',
                password='password',
            )
            assert result is None
        except Exception as exc:
            pytest.fail(f"authenticate raised unexpected exception: {exc}")
