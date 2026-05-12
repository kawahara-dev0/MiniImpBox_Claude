import pytest

from accounts.models import AdminLoginLog


@pytest.mark.django_db
class TestAdminLoginLogModel:
    def test_ordering_is_descending_attempted_at(self):
        assert AdminLoginLog._meta.ordering == ['-attempted_at']

    def test_ip_address_nullable(self):
        field = AdminLoginLog._meta.get_field('ip_address')
        assert field.null is True
        assert field.blank is True

    def test_create_success_log(self):
        log = AdminLoginLog.objects.create(
            email='admin@example.com',
            success=True,
            ip_address='127.0.0.1',
        )
        assert log.pk is not None
        assert log.success is True
        assert log.attempted_at is not None

    def test_create_failure_log_without_ip(self):
        log = AdminLoginLog.objects.create(
            email='unknown@example.com',
            success=False,
            ip_address=None,
        )
        assert log.pk is not None
        assert log.success is False
        assert log.ip_address is None

    def test_email_is_charfield_not_fk(self):
        """email must be a plain CharField, not a FK, to record invalid email attempts."""
        from django.db import models as dj_models
        field = AdminLoginLog._meta.get_field('email')
        assert isinstance(field, dj_models.CharField)
        assert field.max_length == 254
