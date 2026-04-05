from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from notifications.models import UserNotification
from notifications.serializers import UserNotificationSerializer, FCMTokenSerializer

class RegisterFCMTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Notifications"], request=FCMTokenSerializer, responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        request.user.fcm_token = request.data.get('token'); request.user.save(update_fields=['fcm_token'])
        return Response({"message": "FCM token registered"})

class NotificationListView(generics.ListAPIView):
    serializer_class = UserNotificationSerializer; permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Notifications"])
    def get_queryset(self): return UserNotification.objects.filter(user=self.request.user).order_by('-created_at')

class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Notifications"], responses={200: inline_serializer("MarkReadResponse", fields={"message": serializers.CharField()})})
    def post(self, request, notification_id):
        UserNotification.objects.filter(user=request.user, id=notification_id).update(is_read=True, read_at=timezone.now())
        return Response({"message": "Marked read"})

class MarkAllNotificationsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Notifications"], responses={200: inline_serializer("MarkAllReadResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        cnt = UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
        return Response({"message": f"{cnt} notifications marked read"})
