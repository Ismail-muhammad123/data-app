from django.core.management.base import BaseCommand
from orders.services.clubkonnect import ClubKonnectClient

class Command(BaseCommand):
    help = 'Sync networks from ClubKonnect'

    def handle(self, *args, **options):
        self.stdout.write("Syncing networks from ClubKonnect...")
        client = ClubKonnectClient()
        try:
            client.sync_all_services()
            self.stdout.write(self.style.SUCCESS('Networks synced successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

