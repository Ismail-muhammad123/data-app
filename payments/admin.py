# from django.contrib import admin
# from .models import Deposit, Withdrawal

# @admin.register(Deposit)
# class DepositAdmin(admin.ModelAdmin):
#     list_display = (
#         "wallet",
#         "amount",
#         "status",
#         "timestamp",
#         "reference",
#     )
#     list_filter = ('status', 'timestamp')
#     search_fields = ('wallet__user__email',)

# @admin.register(Withdrawal)
# class WithdrawalAdmin(admin.ModelAdmin):
#     list_display = (
#         "wallet",
#         "amount",
#         "status",
#         "timestamp",
#         "reference",
#         "approval_status",
#         "recieving_account_number",
#         "recieving_account_name",
#         "recieving_bank_name",
#     )
#     list_filter = ('status', 'timestamp', 'approval_status')
#     search_fields = ('wallet__user__email',)
#     actions = ['accept_withdrawals']

#     def accept_withdrawals(self, request, queryset):
#         for withdrawal in queryset.filter(status='pending'):
#             pass
#             # withdrawal.status = 'accepted'
#             # withdrawal.save()
#             # Initiate withdrawal logic here (e.g., call payment gateway)
#         self.message_user(request, "Selected withdrawals have been accepted and initiated.")
#     accept_withdrawals.short_description = "Accept selected withdrawals and initiate"