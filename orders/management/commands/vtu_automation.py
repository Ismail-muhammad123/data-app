from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import Purchase, VTUProviderConfig, ServiceRouting
from summary.models import SiteConfig
from orders.router import ProviderRouter
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run periodic VTU automation tasks: detect delays, retry failures, check balances.'

    def handle(self, *args, **options):
        config = SiteConfig.objects.first()
        self.stdout.write(f"Starting VTU Automation Run at {timezone.now()}")
        
        # 1. Detect Delayed Transactions
        if config.delayed_tx_detection_enabled:
            self.detect_delays(config.delayed_tx_timeout_minutes)

        # 2. Auto-Retry Failed Transactions
        if config.auto_retry_enabled:
            self.auto_retry_failed()

        # 3. Check Provider Balances & Trigger Funding Alerts
        self.check_provider_balances()
        
        self.stdout.write(self.style.SUCCESS("Automation Run Completed."))

    def detect_delays(self, timeout_mins):
        self.stdout.write("Checking for delayed transactions...")
        cutoff = timezone.now() - timedelta(minutes=timeout_mins)
        delayed = Purchase.objects.filter(status='pending', time__lt=cutoff)
        
        if delayed.exists():
            for p in delayed:
                self.stdout.write(self.style.WARNING(f"DELAYED: {p.reference} ({p.purchase_type}) to {p.beneficiary} is still pending after {timeout_mins} mins."))
                # Here we could trigger a Slack notification or email
        else:
            self.stdout.write("No delayed transactions detected.")

    def auto_retry_failed(self):
        self.stdout.write("Checking for auto-retryable failures...")
        # Only retry failures from the last 30 minutes to avoid infinite loop or old issues
        cutoff = timezone.now() - timedelta(minutes=30)
        failed_txs = Purchase.objects.filter(status='failed', time__gt=cutoff)
        
        for p in failed_txs:
            routing = ServiceRouting.objects.filter(service=p.purchase_type).first()
            if not routing or not routing.retry_enabled: continue
            
            # Check how many times it already failed (can check logs or provider_response)
            retry_count = p.provider_response.get('retries_done', 0)
            if retry_count < routing.retry_count:
                self.stdout.write(f"RETRYING: {p.reference} (Attempt {retry_count + 1})")
                
                # Execute retry
                res = ProviderRouter.execute_with_fallback(p.purchase_type, f"buy_{p.purchase_type}", **p.provider_response.get('request_data', {}))
                
                if res['status'] == 'SUCCESS':
                    p.status = 'success'
                    self.stdout.write(self.style.SUCCESS(f"RETRY SUCCESS: {p.reference}"))
                else:
                    p.provider_response['retries_done'] = retry_count + 1
                    self.stdout.write(self.style.ERROR(f"RETRY FAILED: {p.reference} - {res.get('message')}"))
                p.save()

    def check_provider_balances(self):
        self.stdout.write("Checking provider balances...")
        active_providers = VTUProviderConfig.objects.filter(is_active=True)
        
        for p in active_providers:
            impl = ProviderRouter.get_provider_implementation(p.name)
            if not impl: continue
            
            try:
                balance = impl.get_wallet_balance()
                self.stdout.write(f" - {p.name}: {balance}")
                
                if balance < p.min_funding_balance:
                    self.stdout.write(self.style.WARNING(f"ALERT: {p.name} balance is LOW ({balance}). Threshold: {p.min_funding_balance}"))
                    
                    if p.auto_funding_enabled:
                         if p.account_number and p.bank_name:
                             self.stdout.write(self.style.NOTICE(f"AUTO-FUND: Provider {p.name} is eligible for funding. Account: {p.account_number} ({p.bank_name})"))
                             # In a real app, logic to trigger a Paystack transfer would go here
                         else:
                             self.stdout.write(self.style.ERROR(f"AUTO-FUND ERROR: Provider {p.name} has auto-funding ON but no account info."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error checking balance for {p.name}: {str(e)}"))
