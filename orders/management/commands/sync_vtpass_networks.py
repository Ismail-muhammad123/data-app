from django.core.management.base import BaseCommand
import requests
from orders.models import AirtimeNetwork, DataNetwork

class Command(BaseCommand):
    help = 'Fetch all available networks from VTPass API and save to database'

    def handle(self, *args, **options):
        # Process airtime networks
        self.process_networks('https://vtpass.com/api/services?identifier=airtime', 'Airtime')

        # Process data networks
        self.process_networks('https://vtpass.com/api/services?identifier=data', 'Data')

        self.stdout.write(self.style.SUCCESS('Networks synced successfully'))

    def process_networks(self, api_url, plan_type):

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            services = response.json().get('content', [])

            for service in services:
                if plan_type == 'Airtime' :
                    network, created = AirtimeNetwork.objects.update_or_create(
                        service_id=service.get('serviceID'),
                        defaults={
                            'name': service.get('name'),
                            'image_url': service.get('image'),
                            'minimum_amount': service.get('minimium_amount', 0),
                            'maximum_amount': service.get('maximum_amount', 0),
                        }
                    )
                elif plan_type == 'Data':
                    network, created = DataNetwork.objects.update_or_create(
                        service_id=service.get('serviceID'),
                        defaults={
                            'name': service.get('name'),
                            'image_url': service.get('image'),
                        }
                    )
                action = 'Created' if created else 'Updated'
                self.stdout.write(f'{action}: {network.name}')

        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f'API Error: {str(e)}'))
