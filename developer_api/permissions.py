from rest_framework import permissions

class IsDeveloperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request, 'developer_profile') and request.developer_profile.is_active
