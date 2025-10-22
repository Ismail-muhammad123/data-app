# from django.db import models
# from django.contrib.auth import get_user_model

# User = get_user_model()

# from wallet.models import Wallet, wallets_transactions
# from savings.models import Savings, SavingsTransaction
# from investments.models import InvestmentAccount, InvestmentTransaction
# from payments.models import Deposit, Withdrawal


# # ---------------------
# # USER SUMMARY PROXY
# # ---------------------
# class UserSummary(User):
#     class Meta:
#         proxy = True
#         verbose_name = "User Summary"
#         verbose_name_plural = "Users Summary"

#     @classmethod
#     def summary(cls):
#         return {
#             "total_users": cls.objects.count(),
#             "new_signups": cls.objects.order_by("-date_joined")[:10],
#             "active_users": cls.objects.filter(is_active=True).count(),
#             "verified_users": cls.objects.filter(is_active=True, is_staff=False).count(),  # adjust as needed
#             "unverified_users": cls.objects.filter(is_active=False).count(),
#         }


# # ---------------------
# # WALLET SUMMARY PROXY
# # ---------------------
# class WalletSummary(Wallet):
#     class Meta:
#         proxy = True
#         verbose_name = "Wallet Summary"
#         verbose_name_plural = "Wallets Summary"

#     @classmethod
#     def summary(cls):
#         from wallet.models import Wallet, wallets_transactions  # adjust import
#         return {
#             "total_wallets": Wallet.objects.count(),
#             "total_balance": Wallet.objects.aggregate(models.Sum("balance"))["balance__sum"] or 0,
#             "total_debits": wallets_transactions.objects.filter(type="debit").aggregate(models.Sum("amount"))["amount__sum"] or 0,
#             "total_credits": wallets_transactions.objects.filter(type="credit").aggregate(models.Sum("amount"))["amount__sum"] or 0,
#         }


# # ---------------------
# # SAVINGS SUMMARY PROXY
# # ---------------------
# class SavingsSummary(Savings):
#     class Meta:
#         proxy = True
#         verbose_name = "Savings Summary"
#         verbose_name_plural = "Savings Summary"

#     @classmethod
#     def summary(cls):
#         return {
#             "total_savings": Savings.objects.aggregate(models.Sum("balance"))["balance__sum"] or 0,
#             "total_credit": SavingsTransaction.objects.filter(type="credit").aggregate(models.Sum("amount"))["amount__sum"] or 0,
#             "total_debit": SavingsTransaction.objects.filter(type="debit").aggregate(models.Sum("amount"))["amount__sum"] or 0,
#         }


# # ---------------------
# # PAYMENTS SUMMARY PROXY
# # ---------------------
# class PaymentSummary(Deposit):
#     class Meta:
#         proxy = True
#         verbose_name = "Payment Summary"
#         verbose_name_plural = "Payments Summary"

#     @classmethod
#     def summary(cls):
#         return {
#             "total_credits": Deposit.objects.aggregate(models.Sum("amount"))["amount__sum"] or 0,
#             "total_debits": Withdrawal.objects.aggregate(models.Sum("amount"))["amount__sum"] or 0,
#             "pending_credits": Deposit.objects.filter(status="pending").count(),
#             "failed_credits": Deposit.objects.filter(status="failed").count(),
#             "successful_credits": Deposit.objects.filter(status="success").count(),
#             "pending_debits": Withdrawal.objects.filter(status="pending").count(),
#             "failed_debits": Withdrawal.objects.filter(status="failed").count(),
#             "successful_debits": Withdrawal.objects.filter(status="success").count(),
#         }


# # ---------------------
# # INVESTMENT SUMMARY PROXY
# # ---------------------
# class InvestmentSummary(InvestmentAccount):
#     class Meta:
#         proxy = True
#         verbose_name = "Investment Summary"
#         verbose_name_plural = "Investments Summary"

#     @classmethod
#     def summary(cls):
#         return {
#             "total_accounts": InvestmentAccount.objects.count(),
#             "total_invested": InvestmentTransaction.objects.filter(transaction_type="deposit").aggregate(models.Sum("amount"))["amount__sum"] or 0,
#             "total_withdrawn": InvestmentTransaction.objects.filter(transaction_type="withdraw").aggregate(models.Sum("amount"))["amount__sum"] or 0,
#             "total_returns": InvestmentTransaction.objects.filter(transaction_type="return").aggregate(models.Sum("amount"))["amount__sum"] or 0,
#         }


from django.db import models
from django.contrib.auth import get_user_model
from wallet.models import Wallet, WalletTransaction
# from savings.models import Savings, SavingsTransaction
from payments.models import Payment
# from investments.models import InvestmentAccount, InvestmentTransaction
from django.db.models import Q
from orders.models import DataPlan, DataNetwork, AirtimeNetwork, Purchase

User = get_user_model()


class SummaryDashboard(Wallet):
    """
    A proxy model that doesn't store data — it aggregates statistics
    from other models across the system.
    """
    class Meta:
        proxy = True
        managed = False
        verbose_name = "Summary Dashboard"
        verbose_name_plural = "Summary Dashboard"

    @classmethod
    def summary(cls, start=None, end=None):
        
        wallets_transactions = WalletTransaction.objects.all()
        purchases = Purchase.objects.all()
        payments = Payment.objects.all()


        # USERS
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_active=True, is_staff=False).count()
        unverified_users = User.objects.filter(is_active=False).count()

        # WALLETS
        if start:
            wallets_transactions = wallets_transactions.filter(timestamp__gte=start)
            purchases = payments.filter(time__gte=start)
            payments = purchases.filter(timestamp__gte=start)

        if end:
            wallets_transactions = wallets_transactions.filter(date__lte=end)
            purchases = payments.filter(time__lte=end)
            payments = purchases.filter(timestamp__lte=end)

        total_wallet_balance = Wallet.objects.aggregate(models.Sum("balance"))["balance__sum"] or 0
        wallet_debits = wallets_transactions.filter(Q(transaction_type="purchase") | Q(transaction_type="withdrawal")).aggregate(models.Sum("amount"))["amount__sum"] or 0
        wallet_credits = wallets_transactions.filter(Q(transaction_type="deposit") | Q(transaction_type="reversal")).aggregate(models.Sum("amount"))["amount__sum"] or 0

        # DATA SALES SUMMARY
        total_purchases = purchases.aggregate(models.Sum("amount"))["amount__sum"] or 0
        data_purchases = purchases.filter(purchase_type='data').aggregate(models.Sum("amount"))["amount__sum"] or 0
        airtime_purchases = purchases.filter(purchase_type='airtime').aggregate(models.Sum("amount"))["amount__sum"] or 0

        data_networks = DataNetwork.objects.all()
        airtime_networks = AirtimeNetwork.objects.all()

        airtime_sales = {}
        # data sales
        for i in airtime_networks:
            airtime_sales[i.name] = purchases.filter(airtime_type=i).aggregate(models.Sum("amount"))["amount__sum"] or 0

        data_sales = {}
        # data sales
        for i in data_networks:
            data_sales[i.name] = purchases.filter(data_plan__service_type=i).aggregate(models.Sum("amount"))["amount__sum"] or 0


        # PAYMENTS
        payments_summary = {
            "credits_total": payments.filter(payment_type="CREDIT").aggregate(models.Sum("amount"))["amount__sum"] or 0,
            "credits_pending": payments.filter(payment_type="CREDIT", status="PENDING").count(),
            "credits_failed": payments.filter(payment_type="CREDIT", status="FAILED").count(),
            "credits_success": payments.filter(payment_type="CREDIT", status="SUCCESS").count(),
        }




        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
                "unverified": unverified_users,
            },
            "wallet": {
                "balance": total_wallet_balance,
                "debits": wallet_debits,
                "credits": wallet_credits,
            },
            "sales": {
                "total": total_purchases,
                "data": data_purchases,
                "airtime": airtime_purchases,
                "data_summary": data_sales,
                "airtime_summary": airtime_sales,
            },
            "payments": payments_summary,
        }

