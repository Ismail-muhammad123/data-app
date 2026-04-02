import requests
import json
import logging
from django.conf import settings
from .models import NotificationProviderConfig, NotificationLog, NotificationTemplate
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
    def send_push(user, title: str, body: str, data: Optional[Dict[str, Any]] = None):
        """
        Send a push notification to a user using the active FCM provider.
        """
        if not user.fcm_token:
            logger.warning(f"User {user.phone_number} has no FCM token.")
            return False

        config = NotificationProviderConfig.objects.filter(provider='fcm', is_active=True).first()
        if not config:
            logger.error("No active FCM provider configured.")
            return False

        server_key = config.config_data.get('server_key')
        if not server_key:
            return False

        provider = FCMProvider(server_key)
        success = provider.send(user.fcm_token, title, body, data)
        
        NotificationLog.objects.create(
            user=user,
            channel='push',
            title=title,
            body=body,
            status='SENT' if success else 'FAILED',
            error_message=None if success else "FCM delivery failed"
        )
        return success

    @staticmethod
    def send_from_template(user, template_slug: str, context: Dict[str, Any]):
        """
        Send a notification using a pre-defined template.
        """
        template = NotificationTemplate.objects.filter(slug=template_slug, is_active=True).first()
        if not template:
            return False

        title = template.title.format(**context)
        body = template.body.format(**context)
        
        return NotificationService.send_push(user, title, body, context)
