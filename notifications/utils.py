import requests
import json
import logging
from django.conf import settings
from .models import NotificationProviderConfig, Notification, UserNotification, NotificationTemplate
from .interfaces import BaseNotificationProvider
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class FCMProvider(BaseNotificationProvider):
    def __init__(self, server_key: str):
        self.server_key = server_key
        self.url = "https://fcm.googleapis.com/fcm/send"
        self.headers = {
            "Authorization": f"key={self.server_key}",
            "Content-Type": "application/json",
        }

    def send(self, recipient_token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> bool:
        payload = {
            "to": recipient_token,
            "notification": {
                "title": title,
                "body": body,
            },
            "data": data or {}
        }
        try:
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=15)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"FCM send error: {e}")
            return False

class NotificationService:
    @staticmethod
    def _get_config(provider_name: str) -> Optional[Dict[str, Any]]:
        config = NotificationProviderConfig.objects.filter(provider=provider_name, is_active=True).first()
        return config.config_data if config else None

    @staticmethod
    def create_notification(users, title: str, body: str, channel: str, data: Optional[Dict[str, Any]] = None) -> Notification:
        """
        Creates a Notification and links it to users via UserNotification.
        Then triggers sending via the selected channel.
        """
        notification = Notification.objects.create(
            title=title,
            body=body,
            channel=channel,
            data=data or {}
        )
        
        user_notifications = []
        for user in users:
            user_notifications.append(UserNotification(
                notification=notification,
                user=user,
                status='PENDING'
            ))
        
        UserNotification.objects.bulk_create(user_notifications)
        
        # Trigger sending (ideally this should be an async task)
        NotificationService.dispatch_notification(notification)
        
        return notification

    @staticmethod
    def dispatch_notification(notification: Notification):
        """
        Loops through all UserNotifications and sends them.
        """
        user_notifications = notification.user_notifications.all()
        channel = notification.channel

        for un in user_notifications:
            success = False
            error_msg = None
            
            try:
                if channel == 'fcm':
                    success = NotificationService.send_push(un.user, notification.title, notification.body, notification.data)
                elif channel == 'sms':
                    success = NotificationService.send_sms(un.user, notification.body)
                elif channel == 'email':
                    success = NotificationService.send_email(un.user, notification.title, notification.body)
                elif channel == 'whatsapp':
                    success = NotificationService.send_whatsapp(un.user, notification.body)
                
                if not success:
                    error_msg = "Provider failed to send"
            except Exception as e:
                success = False
                error_msg = str(e)
            
            un.status = 'SENT' if success else 'FAILED'
            un.error_message = error_msg
            un.save(update_fields=['status', 'error_message'])

    @staticmethod
    def send_push(user, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> bool:
        if not user.fcm_token:
            return False
            
        config = NotificationService._get_config('fcm')
        if not config or 'server_key' not in config:
            return False

        provider = FCMProvider(config['server_key'])
        return provider.send(user.fcm_token, title, body, data)

    @staticmethod
    def send_sms(user, body: str) -> bool:
        from config.utils import TermiiClient
        config = NotificationService._get_config('termii')
        if not config:
            return False
        
        client = TermiiClient(config.get('api_key'), config.get('sender_id'))
        try:
            client.send_otp_sms(user.phone_number, body)
            return True
        except Exception:
            return False

    @staticmethod
    def send_whatsapp(user, body: str) -> bool:
        from config.utils import TermiiClient
        config = NotificationService._get_config('whatsapp') or NotificationService._get_config('termii')
        if not config:
            return False
        
        client = TermiiClient(config.get('api_key'), config.get('sender_id'))
        try:
            client.send_otp_whatsapp(user.phone_number, body)
            return True
        except Exception:
            return False

    @staticmethod
    def send_email(user, title: str, body: str) -> bool:
        if not user.email:
            return False
            
        from django.core.mail import send_mail
        try:
            send_mail(
                title,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def send_from_template(user, template_slug: str, context: Dict[str, Any], channel: str = 'fcm'):
        template = NotificationTemplate.objects.filter(slug=template_slug, is_active=True).first()
        if not template:
            return False

        title = template.title.format(**context)
        body = template.body.format(**context)
        
        return NotificationService.create_notification([user], title, body, channel, context)
