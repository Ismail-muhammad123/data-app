from datetime import datetime
from django.db import transaction
from payments.models import Deposit
from wallet.models import Wallet, WalletTransaction  
import uuid

def fund_wallet(user_id, amount, description="Wallet funded", reference=None, initiator='self', initiated_by=None):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    with transaction.atomic():
        payment_obj = None
        if reference:
            try:
                payment_obj = Deposit.objects.get(reference=reference)
            except Deposit.DoesNotExist:
                pass
        wallet, created = Wallet.objects.get_or_create(user_id=user_id, defaults={'balance': 0.0})
        wallet.balance = wallet.balance + amount
        wallet.save()
        WalletTransaction.objects.create(
            user=wallet.user,
            wallet=wallet,
            transaction_type='credit',
            amount=amount,
            deposit=payment_obj,
            balance_before=float(wallet.balance) - amount,
            balance_after=wallet.balance,
            description=description,
            initiator=initiator,
            initiated_by=initiated_by,
            reference=uuid.uuid4().hex[:10].upper(),
        )
    return wallet.balance

def debit_wallet(user_id, amount, description="Wallet debited", initiator='self', initiated_by=None):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    with transaction.atomic():
        wallet, created = Wallet.objects.get_or_create(user_id=user_id, defaults={'balance': 0.0})
        if wallet.balance < amount:
            raise ValueError("Insufficient balance")
        wallet.balance -= amount
        wallet.save()
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='debit',
            amount=amount,
            timestamp=datetime.now(),
            description=description,
            balance_before=wallet.balance+amount,
            balance_after=wallet.balance,
            initiator=initiator,
            initiated_by=initiated_by,
            user=wallet.user,
            reference=uuid.uuid4().hex[:10].upper(),
        )
    return wallet.balance
