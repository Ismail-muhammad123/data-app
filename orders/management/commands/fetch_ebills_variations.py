from django.core.management.base import BaseCommand
from orders.services.clubkonnect import ClubKonnectClient

class Command(BaseCommand):
    help = 'Fetch product variations from ClubKonnect'

    def handle(self, *args, **options):
        self.stdout.write("Fetching variations from ClubKonnect...")
        client = ClubKonnectClient()
        try:
            client.sync_all_services()
            self.stdout.write(self.style.SUCCESS('Successfully fetched variations from ClubKonnect'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fetching variations: {str(e)}'))