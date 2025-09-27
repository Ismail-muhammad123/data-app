import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


username = os.environ.get("DJANGO_SUPERUSER_USERNAME", None)
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD",None)
full_name = os.environ.get("DJANGO_SUPERUSER_FULL_NAME",None)

class Command(BaseCommand):
    help = 'Creates an initial superuser if one does not exist'

    def handle(self, *args, **kwargs):
        if username is None or password is None or full_name is None:
            self.stdout.write(self.style.WARNING("email, password and full name must all be provided."))            

        User = get_user_model()
        if not User.objects.filter(email=username).exists():
            User.objects.create_superuser(
                phone_number=username,
                password=password,
                full_name=full_name
            )
            self.stdout.write(self.style.SUCCESS("Superuser created."))
        else:
            self.stdout.write(self.style.WARNING("Superuser already exists."))
