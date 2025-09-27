from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display =[
        "wallet", "amount", "status", "timestamp", "reference", "payment_type", "approval_status", ]
    

