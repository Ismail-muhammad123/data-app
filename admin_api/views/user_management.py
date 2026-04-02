from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q, Sum, Count
from drf_spectacular.utils import extend_schema_view, extend_schema
from users.models import User, KYC, StaffPermission
from admin_api.serializers import (
    AdminUserListSerializer, AdminUserDetailSerializer,
    AdminCreateUserRequestSerializer, AdminSetRoleRequestSerializer,
    AdminSetPermissionsRequestSerializer, AdminResetPinRequestSerializer,
    AdminKYCActionRequestSerializer, AdminAgentUpgradeRequestSerializer,
    AdminStatusResponseSerializer, AdminErrorResponseSerializer,
    StaffPermissionSerializer,
)
from admin_api.permissions import CanManageUsers


class UserPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(tags=["Admin User Management"], summary="List all users with pagination, filters, and search"),
    retrieve=extend_schema(tags=["Admin User Management"], summary="Get full user details including wallet, transactions, beneficiaries"),
    partial_update=extend_schema(tags=["Admin User Management"], summary="Update user profile fields"),
    update=extend_schema(tags=["Admin User Management"], summary="Update user profile fields"),
)
class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related('wallet', 'kyc', 'staff_permissions').all().order_by('-created_at')
    permission_classes = [CanManageUsers]
    pagination_class = UserPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['phone_number', 'first_name', 'last_name', 'email', 'referral_code']
    ordering_fields = ['created_at', 'first_name', 'last_name', 'role']
    filterset_fields = ['role', 'is_active', 'is_kyc_verified', 'is_staff', 'is_closed']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminUserDetailSerializer
        if self.action == 'create':
            return AdminCreateUserRequestSerializer
        return AdminUserListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Extra query param filters
        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')
        is_kyc_verified = self.request.query_params.get('is_kyc_verified')
        is_closed = self.request.query_params.get('is_closed')

        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        if is_kyc_verified is not None:
            qs = qs.filter(is_kyc_verified=is_kyc_verified.lower() == 'true')
        if is_closed is not None:
            qs = qs.filter(is_closed=is_closed.lower() == 'true')
        return qs

    # ─── Create User ───

    @extend_schema(
        tags=["Admin User Management"],
        summary="Add a new user",
        request=AdminCreateUserRequestSerializer,
        responses={201: AdminUserDetailSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = AdminCreateUserRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        if User.objects.filter(phone_number=d['phone_number']).exists():
            return Response({"error": "User with this phone number already exists."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            phone_number=d['phone_number'],
            password=d['password'],
            first_name=d.get('first_name', ''),
            last_name=d.get('last_name', ''),
            email=d.get('email'),
            role=d.get('role', 'customer'),
            is_active=d.get('is_active', True),
        )

        # If staff, create permission record
        if user.role == 'staff':
            user.is_staff = True
            user.save(update_fields=['is_staff'])
            StaffPermission.objects.get_or_create(user=user)

        return Response(AdminUserDetailSerializer(user).data, status=status.HTTP_201_CREATED)

    # ─── Activate / Deactivate ───

    @extend_schema(
        tags=["Admin User Management"],
        summary="Activate a user account",
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({"status": "SUCCESS", "message": f"User {user.phone_number} activated."})

    @extend_schema(
        tags=["Admin User Management"],
        summary="Deactivate a user account",
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({"status": "SUCCESS", "message": f"User {user.phone_number} deactivated."})

    # ─── Block / Unblock ───

    @extend_schema(
        tags=["Admin User Management"],
        summary="Block a user (close account)",
        request={"application/json": {"type": "object", "properties": {"reason": {"type": "string"}}}},
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='block')
    def block(self, request, pk=None):
        user = self.get_object()
        user.is_closed = True
        user.is_active = False
        user.closed_at = timezone.now()
        user.closed_reason = request.data.get('reason', 'Blocked by Admin')
        user.save(update_fields=['is_closed', 'is_active', 'closed_at', 'closed_reason'])
        return Response({"status": "SUCCESS", "message": f"User {user.phone_number} blocked."})

    @extend_schema(
        tags=["Admin User Management"],
        summary="Unblock a user (reopen account)",
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='unblock')
    def unblock(self, request, pk=None):
        user = self.get_object()
        user.is_closed = False
        user.is_active = True
        user.closed_at = None
        user.closed_reason = None
        user.save(update_fields=['is_closed', 'is_active', 'closed_at', 'closed_reason'])
        return Response({"status": "SUCCESS", "message": f"User {user.phone_number} unblocked."})

    # ─── KYC ───

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
        user.save(update_fields=['is_kyc_verified'])

        kyc.status = 'APPROVED'
        kyc.time_accepted = timezone.now()
        kyc.remarks = request.data.get('reason', 'Approved by Admin')
        kyc.processed_by = request.user
        kyc.save()

        return Response({"status": "SUCCESS", "message": "User KYC approved."})

    @extend_schema(
        tags=["Admin User Management"],
        summary="Reject user KYC with reason",
        request=AdminKYCActionRequestSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='reject-kyc')
    def reject_kyc(self, request, pk=None):
        user = self.get_object()
        kyc, _ = KYC.objects.get_or_create(user=user)
        user.is_kyc_verified = False
        user.save(update_fields=['is_kyc_verified'])

        kyc.status = 'REJECTED'
        kyc.time_rejected = timezone.now()
        kyc.remarks = request.data.get('reason', 'Rejected by Admin')
        kyc.processed_by = request.user
        kyc.save()

        return Response({"status": "REJECTED", "message": "User KYC rejected."})

    # ─── Reset Transaction PIN ───

    @extend_schema(
        tags=["Admin User Management"],
        summary="Reset or change a user's transaction PIN",
        request=AdminResetPinRequestSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='reset-pin')
    def reset_pin(self, request, pk=None):
        user = self.get_object()
        serializer = AdminResetPinRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_pin = serializer.validated_data['new_pin']
        user.set_transaction_pin(new_pin)
        return Response({"status": "SUCCESS", "message": f"Transaction PIN reset for user {user.phone_number}."})

    # ─── Set Role (Upgrade to Agent / Staff / Downgrade to Customer) ───

    @extend_schema(
        tags=["Admin User Management"],
        summary="Set user role (customer / agent / staff)",
        request=AdminSetRoleRequestSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='set-role')
    def set_role(self, request, pk=None):
        user = self.get_object()
        serializer = AdminSetRoleRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_role = serializer.validated_data['role']
        commission_rate = serializer.validated_data.get('commission_rate', 0.0)

        user.role = new_role
        user.upgraded_at = timezone.now()
        user.upgraded_by = request.user

        if new_role == 'agent':
            user.agent_commission_rate = commission_rate
        elif new_role == 'staff':
            user.is_staff = True
            StaffPermission.objects.get_or_create(user=user)
        else:
            # Downgrade: remove staff flag
            user.is_staff = False

        user.save()
        return Response({"status": "SUCCESS", "message": f"User {user.phone_number} role set to '{new_role}'."})

    # ─── Update Permissions (for staff users) ───

    @extend_schema(
        tags=["Admin User Management"],
        summary="Update staff user permissions",
        request=AdminSetPermissionsRequestSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='set-permissions')
    def set_permissions(self, request, pk=None):
        user = self.get_object()
        if user.role != 'staff' and not user.is_staff:
            return Response({"error": "User is not staff. Set role to 'staff' first."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AdminSetPermissionsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        perms, _ = StaffPermission.objects.get_or_create(user=user)
        for field, value in serializer.validated_data.items():
            setattr(perms, field, value)
        perms.save()

        return Response({"status": "SUCCESS", "message": f"Permissions updated for {user.phone_number}."})

    # ─── Agent Performance ───

    @extend_schema(
        tags=["Admin User Management"],
        summary="View agent performance and commission stats",
        responses={200: {"type": "object"}}
    )
    @action(detail=True, methods=['get'], url_path='agent-performance')
    def agent_performance(self, request, pk=None):
        user = self.get_object()
        from orders.models import Purchase

        today = timezone.now().date()
        purchases = Purchase.objects.filter(user=user, status='success')

        total_sales = purchases.aggregate(total=Sum('amount'))['total'] or 0
        total_count = purchases.count()
        today_sales = purchases.filter(time__date=today).aggregate(total=Sum('amount'))['total'] or 0
        today_count = purchases.filter(time__date=today).count()

        # Per-service breakdown
        by_service = purchases.values('purchase_type').annotate(
            count=Count('id'), total=Sum('amount')
        )

        return Response({
            "user_id": user.id,
            "phone": user.phone_number,
            "role": user.role,
            "commission_rate": float(user.agent_commission_rate),
            "referral_earnings_count": user.referral_earnings_count,
            "referral_earnings_amount": float(user.referral_earnings_amount),
            "total_sales": float(total_sales),
            "total_transactions": total_count,
            "today_sales": float(today_sales),
            "today_transactions": today_count,
            "by_service": list(by_service),
        })

    # ─── Backward-compatible: upgrade-to-agent ───

    @extend_schema(
        tags=["Admin User Management"],
        summary="Upgrade user to agent (legacy)",
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
        return Response({"status": "SUCCESS", "message": f"User {user.phone_number} upgraded to Agent."})
