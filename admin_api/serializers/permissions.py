from rest_framework import serializers
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']


class PermissionSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer(read_only=True)

    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']


class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(), many=True, write_only=True,
        source='permissions', required=False
    )
    users_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'permission_ids', 'users_count']

    def get_users_count(self, obj):
        return obj.user_set.count()

    def create(self, validated_data):
        perms = validated_data.pop('permissions', [])
        group = Group.objects.create(name=validated_data['name'])
        if perms:
            group.permissions.set(perms)
        return group

    def update(self, instance, validated_data):
        perms = validated_data.pop('permissions', None)
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        if perms is not None:
            instance.permissions.set(perms)
        return instance


class GroupListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing groups (no nested permissions)."""
    users_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'users_count']

    def get_users_count(self, obj):
        return obj.user_set.count()


class UserPermissionSummarySerializer(serializers.ModelSerializer):
    """Shows a user's direct permissions and group memberships."""
    groups = GroupListSerializer(many=True, read_only=True)
    user_permissions = PermissionSerializer(many=True, read_only=True)
    all_permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'first_name', 'last_name', 'role',
                  'is_staff', 'is_superuser', 'groups', 'user_permissions', 'all_permissions']

    def get_all_permissions(self, obj):
        """Returns all effective permissions (direct + inherited from groups)."""
        return sorted(list(obj.get_all_permissions()))


class AssignUserPermissionsSerializer(serializers.Serializer):
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False, default=[],
        help_text="List of permission IDs to assign directly to the user. Replaces existing direct permissions."
    )


class AssignUserGroupsSerializer(serializers.Serializer):
    group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False, default=[],
        help_text="List of group IDs to assign to the user. Replaces existing group memberships."
    )
