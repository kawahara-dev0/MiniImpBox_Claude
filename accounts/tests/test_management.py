"""
Test-first tests for accounts management commands.

High-risk area: admin account seed (authentication setup).
All test items are required per roadmap Step 3 acceptance criteria.
"""
import os
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from io import StringIO

User = get_user_model()

SEED_EMAIL = 'seed@example.com'
SEED_PASSWORD = 'seed-password-123'


@pytest.mark.django_db
class TestSeedAdminCommand:
    def _run_seed(self, email=SEED_EMAIL, password=SEED_PASSWORD):
        """Run seed_admin with given credentials via env vars."""
        out = StringIO()
        with patch_env(email, password):
            call_command('seed_admin', stdout=out)
        return out.getvalue()

    def test_creates_user_with_correct_flags(self):
        self._run_seed()
        user = User.objects.get(email=SEED_EMAIL)
        assert user.is_staff is True
        assert user.is_superuser is False
        assert user.is_active is True

    def test_username_set_to_email(self):
        self._run_seed()
        user = User.objects.get(email=SEED_EMAIL)
        assert user.username == SEED_EMAIL

    def test_password_is_hashed_not_plaintext(self):
        self._run_seed()
        user = User.objects.get(email=SEED_EMAIL)
        assert user.password != SEED_PASSWORD
        assert user.password.startswith('pbkdf2_')

    def test_can_authenticate_with_seeded_credentials(self):
        from accounts.backends import EmailBackend
        self._run_seed()
        backend = EmailBackend()
        user = backend.authenticate(
            request=None,
            username=SEED_EMAIL,
            password=SEED_PASSWORD,
        )
        assert user is not None
        assert user.email == SEED_EMAIL

    def test_idempotent_no_duplicate_on_second_run(self):
        self._run_seed()
        self._run_seed()  # second call
        count = User.objects.filter(email=SEED_EMAIL).count()
        assert count == 1

    def test_second_run_outputs_already_exists_warning(self):
        self._run_seed()
        output = self._run_seed()
        assert 'already exists' in output.lower() or 'Admin already exists' in output


import contextlib


@contextlib.contextmanager
def patch_env(email, password):
    old_email = os.environ.get('DJANGO_ADMIN_EMAIL')
    old_password = os.environ.get('DJANGO_ADMIN_PASSWORD')
    os.environ['DJANGO_ADMIN_EMAIL'] = email
    os.environ['DJANGO_ADMIN_PASSWORD'] = password
    try:
        yield
    finally:
        if old_email is None:
            os.environ.pop('DJANGO_ADMIN_EMAIL', None)
        else:
            os.environ['DJANGO_ADMIN_EMAIL'] = old_email
        if old_password is None:
            os.environ.pop('DJANGO_ADMIN_PASSWORD', None)
        else:
            os.environ['DJANGO_ADMIN_PASSWORD'] = old_password
