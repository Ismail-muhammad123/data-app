import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from admin_api.permissions import IsSuperUserOnly
from users.models import User
from wallet.models import WalletTransaction
from payments.models import Deposit, Withdrawal
from orders.models import Purchase
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.utils.dateparse import parse_date

class BaseExportView(APIView):
    permission_classes = [IsAuthenticated, IsSuperUserOnly]

    def get_queryset(self, model_class, date_field='created_at'):
        queryset = model_class.objects.all()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(**{f"{date_field}__date__gte": parse_date(start_date)})
        if end_date:
            queryset = queryset.filter(**{f"{date_field}__date__lte": parse_date(end_date)})
        
        return queryset

    def generate_csv_response(self, filename, headers, data_generator):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(headers)
        for row in data_generator:
            writer.writerow(row)
        return response

class AdminExportUsersView(BaseExportView):
    @extend_schema(
        tags=["Admin Reports"],
        summary="Export users to CSV",
        parameters=[
            OpenApiParameter("start_date", type=str, description="YYYY-MM-DD"),
            OpenApiParameter("end_date", type=str, description="YYYY-MM-DD"),
        ]
    )
    def get(self, request):
        queryset = self.get_queryset(User, date_field='created_at')
        headers = ['ID', 'Phone', 'Email', 'First Name', 'Last Name', 'Role', 'Balance', 'Date Joined']
        
        def data_gen():
            for u in queryset:
                balance = getattr(u, 'wallet', None)
                bal_val = balance.balance if balance else 0
                yield [u.id, u.phone_number, u.email, u.first_name, u.last_name, u.role, bal_val, u.created_at]

        return self.generate_csv_response('users_export', headers, data_gen())

class AdminExportWalletTransactionsView(BaseExportView):
    @extend_schema(
        tags=["Admin Reports"],
        summary="Export wallet transactions to CSV",
        parameters=[
            OpenApiParameter("start_date", type=str, description="YYYY-MM-DD"),
            OpenApiParameter("end_date", type=str, description="YYYY-MM-DD"),
        ]
    )
    def get(self, request):
        queryset = self.get_queryset(WalletTransaction, date_field='timestamp')
        headers = ['ID', 'User', 'Type', 'Amount', 'Before', 'After', 'Description', 'Reference', 'Timestamp']
        
        def data_gen():
            for t in queryset:
                yield [t.id, t.user.phone_number, t.transaction_type, t.amount, t.balance_before, t.balance_after, t.description, t.reference, t.timestamp]

        return self.generate_csv_response('wallet_transactions_export', headers, data_gen())

class AdminExportDepositsView(BaseExportView):
    @extend_schema(
        tags=["Admin Reports"],
        summary="Export deposits to CSV",
        parameters=[
            OpenApiParameter("start_date", type=str, description="YYYY-MM-DD"),
            OpenApiParameter("end_date", type=str, description="YYYY-MM-DD"),
        ]
    )
    def get(self, request):
        queryset = self.get_queryset(Deposit, date_field='timestamp')
        headers = ['ID', 'User', 'Amount', 'Method', 'Status', 'Reference', 'Timestamp']
        
        def data_gen():
            for d in queryset:
                yield [d.id, d.user.phone_number, d.amount, d.payment_type, d.status, d.reference, d.timestamp]

        return self.generate_csv_response('deposits_export', headers, data_gen())

class AdminExportWithdrawalsView(BaseExportView):
    @extend_schema(
        tags=["Admin Reports"],
        summary="Export withdrawals to CSV",
        parameters=[
            OpenApiParameter("start_date", type=str, description="YYYY-MM-DD"),
            OpenApiParameter("end_date", type=str, description="YYYY-MM-DD"),
        ]
    )
    def get(self, request):
        queryset = self.get_queryset(Withdrawal, date_field='created_at')
        headers = ['ID', 'User', 'Amount', 'Bank', 'Account', 'Status', 'Reference', 'Created At']
        
        def data_gen():
            for w in queryset:
                yield [w.id, w.user.phone_number, w.amount, w.bank_name, w.account_number, w.status, w.reference, w.created_at]

        return self.generate_csv_response('withdrawals_export', headers, data_gen())

class AdminExportPurchasesView(BaseExportView):
    @extend_schema(
        tags=["Admin Reports"],
        summary="Export VTU purchases to CSV",
        parameters=[
            OpenApiParameter("start_date", type=str, description="YYYY-MM-DD"),
            OpenApiParameter("end_date", type=str, description="YYYY-MM-DD"),
        ]
    )
    def get(self, request):
        queryset = self.get_queryset(Purchase, date_field='time')
        headers = ['ID', 'User', 'Type', 'Amount', 'Beneficiary', 'Status', 'Reference', 'Provider', 'Time']
        
        def data_gen():
            for p in queryset:
                provider = p.provider.get_name_display() if p.provider else 'N/A'
                yield [p.id, p.user.phone_number, p.purchase_type, p.amount, p.beneficiary, p.status, p.reference, provider, p.time]

        return self.generate_csv_response('purchases_export', headers, data_gen())
