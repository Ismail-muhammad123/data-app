from django.core.management.base import BaseCommand
from orders.services.clubkonnect import ClubKonnectClient

class Command(BaseCommand):
    help = 'Fetch all services and packages from ClubKonnect'

    def handle(self, *args, **options):
        self.stdout.write("Starting ClubKonnect sync...")
        client = ClubKonnectClient()
        try:
            success = client.sync_all_services()
            if success:
                self.stdout.write(self.style.SUCCESS("Successfully synced all services from ClubKonnect"))
            else:
                self.stdout.write(self.style.ERROR("Failed to sync services from ClubKonnect"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
