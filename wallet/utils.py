from datetime import datetime
from django.db import transaction
from wallet.models import Wallet, WalletTransaction  # Adjust import path as needed

# monnify/utils.py

import base64
import hashlib
import hmac
import json
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone




def fund_wallet(user_id, amount, description="Wallet funded"):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    with transaction.atomic():
        wallet, created = Wallet.objects.get_or_create(user_id=user_id, defaults={'balance': 0.0})
        wallet.balance += amount
        wallet.save()
        WalletTransaction.objects.create(
            wallet=wallet,
            type='credit',
            amount=amount,
            timestamp=datetime.now(),
            description=description
        )
    return wallet.balance

def debit_wallet(user_id, amount, description="Wallet debited"):
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
            type='debit',
            amount=amount,
            timestamp=datetime.now(),
            description=description
        )
    return wallet.balance
