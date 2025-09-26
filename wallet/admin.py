from django.contrib import admin
from .models import WalletTransaction, Wallet

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
