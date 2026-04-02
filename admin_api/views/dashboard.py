from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from users.models import User
from payments.models import Deposit
from orders.models import Purchase
from admin_api.serializers import AdminDashboardStatsResponseSerializer


class AdminDashboardStatsView(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Admin Dashboard"],
        summary="Dashboard overview statistics",
        description="Returns high-level stats: total users, total deposits, total purchases.",
        responses={200: AdminDashboardStatsResponseSerializer}
    )
    def get(self, request):
        today = timezone.now().date()
        total_users = User.objects.count()
        total_deposits = Deposit.objects.filter(status='SUCCESS').aggregate(Sum('amount'))['amount__sum'] or 0
        total_purchases = Purchase.objects.count()
        
        return Response({
            "users": {"total": total_users},
            "finances": {"total_deposits": total_deposits},
            "transactions": {"total": total_purchases}
        })
