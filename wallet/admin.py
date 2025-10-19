from django.contrib import admin
from .models import WalletTransaction, Wallet, VirtualAccount
from django.contrib import messages


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

    def has_change_permission(self, request, obj = ...):
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


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'balance_before', 'balance_after', 'timestamp', 'reference')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('user__email', 'reference', 'description')
    readonly_fields = ('timestamp',)
