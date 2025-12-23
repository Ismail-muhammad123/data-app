# vtpass_integration/management/commands/sync_vtpass_plans.py
from django.core.management.base import BaseCommand
# from django.db import transaction
# from django.utils import timezone
import logging
import requests
# from orders.utils import list_services, get_service_variations
from orders.models import DataPlan, DataNetwork  # adjust import to where your Plan model is
# from decimal import Decimal

logger = logging.getLogger(__name__)

# map VTpass service ids to our Plan.service_type value (optional)
SERVICE_TYPE_MAPPING = {
    "mtn-airtime": "airtime",
    "glo-airtime": "airtime",
    "airtel-airtime": "airtime",
    "9mobile-airtime": "airtime",
    "mtn-data": "data",
    "glo-data": "data",
    "airtel-data": "data",
    "9mobile-data": "data",
    "smile-direct": "smile",
}


class Command(BaseCommand):
    help = "Sync plans from VTpass into Plan model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--services",
            nargs="+",
            help="Optional list of serviceIDs to sync. If omitted, syncs the default set.",
        )

    def handle(self, *args, **options):

        synced = 0

         # 1) load data plan types
        data_types = DataNetwork.objects.all()

        if not len(data_types):
            logger.warning("No Data Plan types found for variations")
            return

        # 2) create Plan for each of the result, if not already there
        for data_type in data_types:
            logger.info("Loading Variations for %s", data_type.name)
            response = requests.get(f"https://vtpass.com/api/service-variations?serviceID={data_type.service_id}")
            response.raise_for_status()
            if response.json().get('response_description') != '000':
                logger.error("Error fetching variations for Data Plan Type: %s. ID: %s", data_type.name, data_type.service_id)
                continue
            variations = response.json()['content']['variations']

            if not len(variations):
                logger.warning("No Variations found for Data Plan Type: %s", data_types.name)
                continue

            # 3) create DataPlan for each variation or update existing one.
            for variation in variations:
                plan, created = DataPlan.objects.get_or_create(
                    service_type=data_type, 
                    variation_code=variation['variation_code'], 
                    defaults={
                        "name": variation['name'],
                        "description": "",
                        "cost_price": round(float(variation['variation_amount'])),
                        "selling_price": round(float(variation['variation_amount'])),
                    }    
                )
                # if not created:
                plan.is_active = True
                plan.save()
                synced += 1

        self.stdout.write(self.style.SUCCESS(f"Synced {synced} variations."))
