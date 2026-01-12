from django.core.management.base import BaseCommand
from orders.models import DataVariation, DataService
from orders.utils.ebills_client import EBillsClient

class Command(BaseCommand):
    help = 'Fetch product variations'

    def handle(self, *args, **options):

        client = EBillsClient()

        # Authenticate
        client.authenticate()

        variations = client.get_data_variations()

        print(type(variations))

        variations = variations.get('data', [])

        for variation in variations:
            service, created = DataService.objects.get_or_create(
                service_id=variation["service_id"],
                defaults={
                    "service_name": variation["service_name"],
                }
            )
            
            variation, created = DataVariation.objects.update_or_create(
                variation_id=variation["variation_id"],
                defaults={
                    "name": variation['data_plan'],
                    "service": service,
                    "variation_id": variation["variation_id"],
                    "cost_price": variation["reseller_price"],
                    "selling_price": variation["price"],
                    "is_active": variation["availability"] == "Available",
                }
            )

            self.stdout.write(f'{"Created" if created else "Updated"} {variation.id}: {variation.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully fetched {len(variations)} variations'
            )
        )