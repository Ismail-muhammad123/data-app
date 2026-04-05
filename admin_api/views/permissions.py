from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema_view, extend_schema, inline_serializer, OpenApiParameter
from admin_api.permissions import IsSuperUserOnly
from admin_api.serializers.permissions import (
    PermissionSerializer, GroupSerializer, GroupListSerializer,
    UserPermissionSummarySerializer, AssignUserPermissionsSerializer,
    AssignUserGroupsSerializer
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────
# 1. List All Available Permissions
# ─────────────────────────────────────────────────────────────────────
@extend_schema_view(
    list=extend_schema(summary="List all available permissions", tags=["Admin Permissions & Groups"]),
    retrieve=extend_schema(summary="Get permission details", tags=["Admin Permissions & Groups"]),
)
class AdminPermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset to list all Django permissions.
    Admins can browse this list to know which permission IDs to assign.
    """
    queryset = Permission.objects.select_related('content_type').all().order_by('content_type__app_label', 'codename')
    serializer_class = PermissionSerializer
    permission_classes = [IsSuperUserOnly]
    pagination_class = None  # Return all permissions without pagination


# ─────────────────────────────────────────────────────────────────────
# 2. Full CRUD for Groups
# ─────────────────────────────────────────────────────────────────────
@extend_schema_view(
    list=extend_schema(summary="List all groups", tags=["Admin Permissions & Groups"]),
    create=extend_schema(summary="Create a new group", tags=["Admin Permissions & Groups"]),
    retrieve=extend_schema(summary="Get group details with permissions", tags=["Admin Permissions & Groups"]),
    update=extend_schema(summary="Fully update a group", tags=["Admin Permissions & Groups"]),
    partial_update=extend_schema(summary="Partially update a group", tags=["Admin Permissions & Groups"]),
    destroy=extend_schema(summary="Delete a group", tags=["Admin Permissions & Groups"]),
)
class AdminGroupViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for permission groups.
    When creating/updating, pass `permission_ids` (list of ints) to set the group's permissions.
    """
    queryset = Group.objects.prefetch_related('permissions', 'permissions__content_type').all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [IsSuperUserOnly]
    pagination_class = None

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({"message": f"Group '{name}' deleted successfully."}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────
# 3. User Permission Management
# ─────────────────────────────────────────────────────────────────────
class AdminUserPermissionView(APIView):
    """
    View and update the permissions and groups for a specific user.
    Supports lookup by user ID or phone number via query parameter.
    """
    permission_classes = [IsSuperUserOnly]

    def _get_user(self, identifier):
        """Resolve a user from an ID or phone number."""
        if identifier.isdigit():
            return get_object_or_404(User, pk=int(identifier))
        return get_object_or_404(User, phone_number=identifier)

    @extend_schema(
        summary="Get permissions and groups for a user",
        description="Fetch a user's direct permissions, group memberships, and all effective permissions. "
                    "Pass user ID or phone number as the path parameter.",
        tags=["Admin Permissions & Groups"],
        responses={200: UserPermissionSummarySerializer}
    )
    def get(self, request, identifier):
        user = self._get_user(identifier)
        return Response(UserPermissionSummarySerializer(user).data)

    @extend_schema(
        summary="Update direct permissions for a user",
        description="Replaces all direct permissions for the user with the provided list. "
                    "Pass user ID or phone number as the path parameter.",
        tags=["Admin Permissions & Groups"],
        request=AssignUserPermissionsSerializer,
        responses={200: UserPermissionSummarySerializer}
    )
    def put(self, request, identifier):
        user = self._get_user(identifier)
        serializer = AssignUserPermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        perm_ids = serializer.validated_data['permission_ids']
        permissions = Permission.objects.filter(id__in=perm_ids)
        if len(permissions) != len(perm_ids):
            return Response({"error": "One or more permission IDs are invalid."}, status=400)

        user.user_permissions.set(permissions)
        return Response(UserPermissionSummarySerializer(user).data)


class AdminUserGroupView(APIView):
    """
    View and update group memberships for a specific user.
    Supports lookup by user ID or phone number.
    """
    permission_classes = [IsSuperUserOnly]

    def _get_user(self, identifier):
        if identifier.isdigit():
            return get_object_or_404(User, pk=int(identifier))
        return get_object_or_404(User, phone_number=identifier)

    @extend_schema(
        summary="Get groups for a user",
        description="Fetch a user's current group memberships. "
                    "Pass user ID or phone number as the path parameter.",
        tags=["Admin Permissions & Groups"],
        responses={200: GroupListSerializer(many=True)}
    )
    def get(self, request, identifier):
        user = self._get_user(identifier)
        groups = user.groups.all()
        return Response(GroupListSerializer(groups, many=True).data)

    @extend_schema(
        summary="Update groups for a user",
        description="Replaces all group memberships for the user with the provided list. "
                    "Pass user ID or phone number as the path parameter.",
        tags=["Admin Permissions & Groups"],
        request=AssignUserGroupsSerializer,
        responses={200: UserPermissionSummarySerializer}
    )
    def put(self, request, identifier):
        user = self._get_user(identifier)
        serializer = AssignUserGroupsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group_ids = serializer.validated_data['group_ids']
        groups = Group.objects.filter(id__in=group_ids)
        if len(groups) != len(group_ids):
            return Response({"error": "One or more group IDs are invalid."}, status=400)

        user.groups.set(groups)
        return Response(UserPermissionSummarySerializer(user).data)
