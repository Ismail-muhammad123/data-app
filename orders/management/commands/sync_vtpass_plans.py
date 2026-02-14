from django.core.management.base import BaseCommand
from orders.services.clubkonnect import ClubKonnectClient

class Command(BaseCommand):
    help = "Sync plans from ClubKonnect into DataVariation model"

    def handle(self, *args, **options):
        self.stdout.write("Syncing plans from ClubKonnect...")
        client = ClubKonnectClient()
        try:
            client.sync_all_services()
            self.stdout.write(self.style.SUCCESS("Successfully synced all plans from ClubKonnect"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))

