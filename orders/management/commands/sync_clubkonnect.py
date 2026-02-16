from django.core.management.base import BaseCommand
from orders.services.clubkonnect import ClubKonnectClient

class Command(BaseCommand):
    help = 'Fetch services and packages from ClubKonnect'

    def add_arguments(self, parser):
        parser.add_argument(
            '--service',
            type=str,
            help='Specify a service to sync (airtime, data, cable, electricity, smile)',
        )

    def handle(self, *args, **options):
        service = options.get('service')
        client = ClubKonnectClient()
        
        try:
            if service:
                if service == 'airtime':
                    client.sync_airtime()
                elif service == 'data':
                    client.sync_data()
                elif service == 'cable':
                    client.sync_cable()
                elif service == 'electricity':
                    client.sync_electricity()
                elif service == 'smile':
                    client.sync_smile()
                else:
                    self.stdout.write(self.style.ERROR(f"Unknown service: {service}"))
                    return
                self.stdout.write(self.style.SUCCESS(f"Successfully synced {service} from ClubKonnect"))
            else:
                self.stdout.write("Starting full ClubKonnect sync...")
                success = client.sync_all_services()
                if success:
                    self.stdout.write(self.style.SUCCESS("Successfully synced all services from ClubKonnect"))
                else:
                    self.stdout.write(self.style.ERROR("Failed to sync services from ClubKonnect"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))

