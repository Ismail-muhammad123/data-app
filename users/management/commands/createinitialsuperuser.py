import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Creates an initial superuser if one does not exist'

    def handle(self, *args, **kwargs):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        full_name = os.environ.get("DJANGO_SUPERUSER_FULL_NAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")

        if not username or not password or not full_name:
            self.stdout.write(self.style.ERROR("DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD, and DJANGO_SUPERUSER_FULL_NAME must all be provided."))
            return

        User = get_user_model()
        if not User.objects.filter(phone_number=username).exists():
            User.objects.create_superuser(
                phone_number=username,
                password=password,
                email=email if email else None
            )
            self.stdout.write(self.style.SUCCESS(f"Superuser {username} created successfully."))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser with phone number {username} already exists."))
