from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from drf_spectacular.utils import extend_schema_view, extend_schema
from users.models import User, KYC
from admin_api.serializers import (
    AdminUserSerializer, AdminKYCActionRequestSerializer,
    AdminAgentUpgradeRequestSerializer, AdminStatusResponseSerializer,
    AdminErrorResponseSerializer
)
from admin_api.permissions import CanManageUsers

@extend_schema_view(
    list=extend_schema(tags=["Admin User Management"]),
    retrieve=extend_schema(tags=["Admin User Management"]),
    partial_update=extend_schema(tags=["Admin User Management"]),
    update=extend_schema(tags=["Admin User Management"]),
)
class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = AdminUserSerializer
    permission_classes = [CanManageUsers]

    @extend_schema(
        tags=["Admin User Management"],
        summary="Approve user KYC",
        request=AdminKYCActionRequestSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='approve-kyc')
    def approve_kyc(self, request, pk=None):
        user = self.get_object()
        kyc, _ = KYC.objects.get_or_create(user=user)
        user.is_kyc_verified = True
        user.save()
        
        kyc.status = 'APPROVED'
        kyc.time_accepted = timezone.now()
        kyc.remarks = request.data.get('reason', 'Approved by Admin')
        kyc.processed_by = request.user
        kyc.save()
        
        return Response({"status": "SUCCESS", "message": "User KYC approved."})

    @extend_schema(
        tags=["Admin User Management"],
        summary="Reject user KYC",
        request=AdminKYCActionRequestSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='reject-kyc')
    def reject_kyc(self, request, pk=None):
        user = self.get_object()
        kyc, _ = KYC.objects.get_or_create(user=user)
        user.is_kyc_verified = False
        user.save()
        
        kyc.status = 'REJECTED'
        kyc.time_rejected = timezone.now()
        kyc.remarks = request.data.get('reason', 'Rejected by Admin')
        kyc.processed_by = request.user
        kyc.save()
        
        return Response({"status": "REJECTED", "message": "User KYC rejected."})

    @extend_schema(
        tags=["Admin User Management"],
        summary="Upgrade user to agent",
        request=AdminAgentUpgradeRequestSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='upgrade-to-agent')
    def upgrade_to_agent(self, request, pk=None):
        user = self.get_object()
        user.role = 'agent'
        user.agent_commission_rate = request.data.get('commission_rate', 0.0)
        user.upgraded_at = timezone.now()
        user.upgraded_by = request.user
        user.save()
        return Response({"status": "User upgraded to Agent"})
