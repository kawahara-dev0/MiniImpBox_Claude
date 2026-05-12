import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create the initial admin account from environment variables.'

    def handle(self, *args, **options):
        email    = os.environ['DJANGO_ADMIN_EMAIL']
        password = os.environ['DJANGO_ADMIN_PASSWORD']
        User = get_user_model()

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'Admin already exists: {email}'))
            return

        User.objects.create_user(
            username=email,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=False,
            is_active=True,
        )
        self.stdout.write(self.style.SUCCESS(f'Admin created: {email}'))
