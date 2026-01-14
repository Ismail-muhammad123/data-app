from django.core.management.base import BaseCommand
from orders.models import DataVariation, DataService, ElectricityService, TVService, TVVariation
from orders.utils.ebills_client import EBillsClient

class Command(BaseCommand):
    help = 'Fetch product variations'

    def handle(self, *args, **options):

        client = EBillsClient()

        # Authenticate
        client.authenticate()

        # Fetch Data Variations
        variations = client.get_data_variations()

        variations = variations.get('data', [])

        print("Creating/Updating Data Variations...")
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
        print("Data Variations sync complete.")
        print("-----------------------------------")

        print("Creating/Updating Cable/TV variations.")
        tv_variations = client.tv_variations().get('data', [])
        for variation in tv_variations:
            service, created = TVService.objects.get_or_create(
                service_id=variation["service_id"],
                defaults={
                    "service_name": variation["service_name"],
                }
            )
            
            variation, created = TVVariation.objects.update_or_create(
                variation_id=variation["variation_id"],
                defaults={
                    "name": variation['package_bouquet'],
                    "package_bouquet": variation['package_bouquet'],
                    "service": service,
                    "variation_id": variation["variation_id"],
                    "selling_price": variation["price"],
                    "is_active": variation["availability"] == "Available",
                }
            )

            self.stdout.write(f'{"Created" if created else "Updated"} {variation.id}: {variation.name}')
        print("TV Variations sync complete.")
        print("-----------------------------------")

        print("Creating/Updating Electricity variations.")
        electricity_variations = client.electricity_variations()
        for variation in electricity_variations:
            service_id = variation["service_id"]
            service_name = variation["name"]

            service, created = ElectricityService.objects.get_or_create(
                service_id=service_id,
                defaults={"service_name": service_name},
            )

            self.stdout.write(f'{"Created" if created else "Updated"} {service.id}: {service.service_name}')
        print("Electricity Variations sync complete.")
        print("-----------------------------------")




        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully fetched {len(variations)} variations'
            )
        )