
import requests
import json
import logging
from django.conf import settings
from .models import Notification, UserNotification, NotificationTemplate
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class FCMProvider:
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
    def create_notification(users, title: str, body: str, channel: str, data: Optional[Dict[str, Any]] = None, created_by=None) -> Notification:
        notification = Notification.objects.create(
            title=title,
            body=body,
            channel=channel,
            data=data or {},
            created_by=created_by
        )
        
        user_notifications = []
        for user in users:
            user_notifications.append(UserNotification(
                notification=notification,
                user=user,
                status='PENDING'
            ))
        
        UserNotification.objects.bulk_create(user_notifications)
        NotificationService.dispatch_notification(notification)
        return notification

    @staticmethod
    def dispatch_notification(notification: Notification):
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
            
        fcm_key = getattr(settings, 'FCM_SERVER_KEY', None)
        if not fcm_key:
            return False

        provider = FCMProvider(fcm_key)
        return provider.send(user.fcm_token, title, body, data)

    @staticmethod
    def send_sms(user, body: str) -> bool:
        # Using Zoho SMS via generic endpoint or integration
        zoho_api_key = getattr(settings, 'ZOHO_SMS_API_KEY', None)
        if not zoho_api_key:
            return False
            
        # Implementation for Zoho SMS sending
        try:
            # Placeholder for Zoho SMS API call
            # response = requests.post("https://sms.zoho.com/api/v2/send", ...)
            return True
        except Exception:
            return False

    @staticmethod
    def send_whatsapp(user, body: str) -> bool:
        # Using Zoho WhatsApp
        zoho_wa_api_key = getattr(settings, 'ZOHO_WHATSAPP_API_KEY', None)
        if not zoho_wa_api_key:
            return False
            
        try:
            # Placeholder for Zoho WhatsApp API call
            return True
        except Exception:
            return False

    @staticmethod
    def send_email(user, title: str, body: str) -> bool:
        if not user.email:
            return False

        zepto_token = getattr(settings, 'ZEPTO_MAIL_TOKEN', None)
        from_email = getattr(settings, 'ZEPTO_FROM_EMAIL', 'noreply@example.com')
        from_name = getattr(settings, 'ZEPTO_FROM_NAME', 'DataApp')

        if not zepto_token:
            logger.error("ZEPTO_MAIL_TOKEN not configured")
            return False

        try:
            response = requests.post(
                "https://api.zeptomail.com/v1.1/email",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": zepto_token,
                },
                json={
                    "from": {"address": from_email, "name": from_name},
                    "to": [{"email_address": {"address": user.email, "name": getattr(user, 'full_name', user.email)}}],
                    "subject": title,
                    "htmlbody": f"<div>{body}</div>",
                },
                timeout=15,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ZeptoMail send error: {e}")
            return False

    @staticmethod
    def send_from_template(user, template_slug: str, context: Dict[str, Any]):
        """
        Sends notifications to a user based on a template and active channels.
        Checks both SiteConfig (global toggles) and NotificationTemplate (template toggles).
        """
        from summary.models import SiteConfig
        
        template = NotificationTemplate.objects.filter(slug=template_slug, is_active=True).first()
        if not template:
            logger.warning(f"Notification template not found or inactive: {template_slug}")
            return False

        config = SiteConfig.objects.first()
        if not config:
            logger.warning("SiteConfig not found, skipping notifications")
            return False

        # Format content
        try:
            title = template.title.format(**context)
            body = template.body.format(**context)
        except KeyError as e:
            logger.error(f"Missing context key {e} for template {template_slug}")
            # Fallback to unformatted if formatting fails
            title = template.title
            body = template.body

        # Determine active channels
        channels_to_send = []
        if config.fcm_enabled and template.use_fcm:
            channels_to_send.append('fcm')
        if config.email_enabled and template.use_email:
            channels_to_send.append('email')
        if config.sms_enabled and template.use_sms:
            channels_to_send.append('sms')
        if config.whatsapp_enabled and template.use_whatsapp:
            channels_to_send.append('whatsapp')

        if not channels_to_send:
            logger.info(f"No active channels for template {template_slug}")
            return False

        results = []
        for channel in channels_to_send:
            res = NotificationService.create_notification([user], title, body, channel, context)
            results.append(res)
        
        return len(results) > 0

    @staticmethod
    def broadcast_announcement(title: str, body: str, channel: str = 'fcm', data: Optional[Dict[str, Any]] = None, created_by=None):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.filter(is_active=True)
        return NotificationService.create_notification(users, title, body, channel, data, created_by=created_by)
