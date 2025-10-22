from .models import WalletTransaction, Wallet, VirtualAccount
from django.contrib import messages
from django.contrib import admin, messages
from django.utils import timezone
from django import forms
from decimal import Decimal
import uuid
from django.db import models, transaction


from .models import WalletTransaction, Wallet
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(VirtualAccount)
class VirtualAccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "account_number",
        "bank_name",
        "account_reference",
        "customer_email",
        "customer_name",
        "status",
        "created_at",
    )

    def has_change_permission(self, request):
        return False
    
    def has_add_permission(self, request):
        return False

    def deactivate_accounts(modeladmin, request, queryset):
        updated = queryset.update(status="INACTIVE")
        messages.success(request, f"{updated} account(s) deactivated successfully.")
    deactivate_accounts.short_description = "Deactivate selected virtual accounts"

    actions = [deactivate_accounts]




class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ('timestamp', 'balance_before', 'balance_after', 'reference')

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user','balance','updated_at','created_at')
    sortable_by = ('balance', 'updated_at', 'created_at')
    readonly_fields = ('balance', 'updated_at', 'created_at')

    inlines = [WalletTransactionInline]



# -------------------------------
# Admin Form (customized form logic)
# -------------------------------
class WalletTransactionAdminForm(forms.ModelForm):
    # Add custom field for user phone number
    user_phone = forms.CharField(
        label="User Phone Number",
        help_text="Enter the user's phone number (username).",
    )

    class Meta:
        model = WalletTransaction
        fields = ["user_phone", "transaction_type", "amount", "description"]

    def clean_user_phone(self):
        phone = self.cleaned_data["user_phone"]
        if str(phone).startswith("0"):
            phone = phone[1:]
        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            raise forms.ValidationError(f"No user found with phone number {phone}")
        self.cleaned_data["user"] = user
        return phone

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        if user:
            wallet = Wallet.objects.filter(user=user).first()
            if not wallet:
                raise forms.ValidationError("This user does not have a wallet.")
            cleaned_data["wallet"] = wallet
        return cleaned_data


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    form = WalletTransactionAdminForm

    list_display = (
        "user",
        "wallet",
        "transaction_type",
        "amount",
        "balance_before",
        "balance_after",
        "reference",
        "timestamp",
    )
    readonly_fields = (
        "wallet",
        "balance_before",
        "balance_after",
        "reference",
        "timestamp",
        "initiator",
        "initiated_by",
    )

    search_fields = ("user__username", "reference")
    list_filter = ("transaction_type", "initiator")

    def has_change_permission(self, request, obj = ...):
        return False
    
    def has_delete_permission(self, request, obj = ...):
        return False

    def save_model(self, request, obj, form, change):
        obj.user = form.cleaned_data["user"]
        obj.wallet = form.cleaned_data["wallet"]
        obj.initiated_by = request.user
        obj.initiator = "admin"
        obj.reference = f"ADM-{uuid.uuid4().hex[:10].upper()}"
        obj.timestamp = timezone.now()

        try:
            wallet = obj.wallet
            if not wallet:
                raise ValueError("Wallet not found")

            obj.balance_before = wallet.balance

            if obj.transaction_type in ['deposit', 'reversal']:
                wallet.balance += obj.amount
            elif obj.transaction_type in ['withdrawal', 'purchase']:
                if wallet.balance < obj.amount:
                    raise ValueError("Insufficient funds")
                wallet.balance -= obj.amount

            obj.balance_after = wallet.balance

            # Save both atomically
            with transaction.atomic():
                wallet.save(update_fields=["balance"])
                obj.save()
                messages.success(request, f"✅ Transaction applied and wallet updated for {obj.user.full_name} - {obj.user.phone_number}.")
        except Exception as e:
            messages.error(request, f"❌ Transaction failed: {e}")

    
