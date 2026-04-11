
import requests
import json
import logging
from django.conf import settings
from .models import Notification, UserNotification, NotificationTemplate
from typing import Optional, Dict, Any
from config.utils import send_sms_message

from decimal import Decimal
from datetime import date, datetime
import django.db.models as dj_models

logger = logging.getLogger(__name__)

def _json_safe(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dj_models.Model):
        return getattr(value, "id", str(value))
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value

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
    def _is_channel_enabled(channel: str) -> bool:
        """
        Enforce global channel toggles from SiteConfig for every dispatch path
        (template-based and direct create_notification/bulk-send paths).
        """
        try:
            from summary.models import SiteConfig
            config = SiteConfig.objects.first()
            if not config:
                return True

            mapping = {
                "fcm": config.fcm_enabled,
                "email": config.email_enabled,
                "sms": config.sms_enabled,
                "whatsapp": config.whatsapp_enabled,
            }
            return mapping.get(channel, True)
        except Exception:
            return True

    @staticmethod
    def create_notification(users, title: str, body: str, channel: str, data: Optional[Dict[str, Any]] = None, created_by=None) -> Notification:
        notification = Notification.objects.create(
            title=title,
            body=body,
            channel=channel,
            data=_json_safe(data) or {},
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
                if not NotificationService._is_channel_enabled(channel):
                    success = False
                    error_msg = f"{channel} channel is disabled in SiteConfig"
                    un.status = 'FAILED'
                    un.error_message = error_msg
                    un.save(update_fields=['status', 'error_message'])
                    continue

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
        phone_number = f"{getattr(user, 'phone_country_code', '')}{getattr(user, 'phone_number', '')}".strip()
        if not phone_number:
            return False
        return send_sms_message(phone_number, body)

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
        If database template is missing, it uses a hardcoded fallback.
        """
        from summary.models import SiteConfig
        
        # Hardcoded Fallbacks
        FALLBACK_TEMPLATES = {
            # Wallet & Transactions
            "wallet-funded": {
                "title": "Wallet Funded Successfully",
                "body": "Your wallet has been credited with N{amount}. Your new balance is N{balance}.",
            },
            "wallet-debit": {
                "title": "Wallet Debited",
                "body": "Your wallet has been debited with N{amount} for {reason}. Your new balance is N{balance}.",
            },
            "wallet-transfer-sent": {
                "title": "Transfer Successful",
                "body": "Your transfer of N{amount} to {recipient} was successful.",
            },
            "wallet-transfer-received": {
                "title": "Funds Received",
                "body": "You have received N{amount} from {sender}. Your new balance is N{balance}.",
            },

            # Order Processing
            "purchase-failed": {
                "title": "Purchase Failed",
                "body": "Your {service} purchase for {beneficiary} failed. N{amount} has been refunded to your wallet.",
            },
            "purchase-success": {
                "title": "Purchase Successful",
                "body": "Your {service} purchase for {beneficiary} of N{amount} was successful. Ref: {reference}.",
            },
            "transaction-reversed": {
                "title": "Transaction Reversed",
                "body": "Your transaction for {service} ({reference}) has been reversed. N{amount} has been credited back to your wallet.",
            },

            # Withdrawals
            "withdrawal-initiated": {
                "title": "Withdrawal Initiated",
                "body": "Your withdrawal request of N{amount} to {bank_name} is being processed. Ref: {reference}.",
            },
            "withdrawal-success": {
                "title": "Withdrawal Successful",
                "body": "Your withdrawal of N{amount} to {bank_name} has been completed successfully.",
            },
            "withdrawal-failed": {
                "title": "Withdrawal Failed",
                "body": "Your withdrawal request of N{amount} failed. The amount has been refunded to your wallet. Reason: {reason}.",
            },

            # KYC & Account
            "kyc-submitted": {
                "title": "KYC Documents Received",
                "body": "Your KYC documents have been submitted and are under review. We will notify you once verified.",
            },
            "kyc-approved": {
                "title": "KYC Verified!",
                "body": "Congratulations! Your KYC verification is successful. Your account limits have been updated.",
            },
            "kyc-rejected": {
                "title": "KYC Verification Failed",
                "body": "Your KYC verification was rejected. Reason: {reason}. Please re-submit the correct documents.",
            },

            # Security
            "security-pin-changed": {
                "title": "Transaction PIN Updated",
                "body": "Your transaction PIN has been successfully changed. If you didn't do this, please contact support immediately.",
            },
            "security-password-changed": {
                "title": "Account Password Changed",
                "body": "Your account password was updated successfully.",
            },
            "security-login-alert": {
                "title": "New Login Detected",
                "body": "A new login was detected on your account from {device} in {location}. If this wasn't you, secure your account.",
            },

            # Admin Actions
            "account-blocked": {
                "title": "Account Blocked",
                "body": "Your account has been blocked. Reason: {reason}. Please contact support if you believe this is an error.",
            },
            "account-unblocked": {
                "title": "Account Unblocked",
                "body": "Your account has been unblocked. you can now log in and continue your transactions.",
            },
            "transaction-pin-reset": {
                "title": "Transaction PIN Reset",
                "body": "Your transaction PIN has been reset by an administrator.",
            },
            "login-pin-reset": {
                "title": "Login PIN Reset",
                "body": "Your login PIN has been reset by an administrator.",
            }
        }

        template = NotificationTemplate.objects.filter(slug=template_slug, is_active=True).first()
        
        if not template:
            if template_slug in FALLBACK_TEMPLATES:
                logger.info(f"Using hardcoded fallback for template: {template_slug}")
                title_tpl = FALLBACK_TEMPLATES[template_slug]["title"]
                body_tpl = FALLBACK_TEMPLATES[template_slug]["body"]
                # For fallbacks, we use a default set of channels if site config allows
                use_fcm = True
                use_email = True
                use_sms = False
                use_whatsapp = False
            else:
                logger.warning(f"Notification template not found or inactive: {template_slug}")
                return False
        else:
            title_tpl = template.title
            body_tpl = template.body
            use_fcm = template.use_fcm
            use_email = template.use_email
            use_sms = template.use_sms
            use_whatsapp = template.use_whatsapp

        config = SiteConfig.objects.first()
        if not config:
            logger.warning("SiteConfig not found, skipping notifications")
            return False

        # Format content
        try:
            title = title_tpl.format(**context)
            body = body_tpl.format(**context)
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Formatting error for template {template_slug}: {e}")
            title = title_tpl
            body = body_tpl

        # Determine active channels
        channels_to_send = []
        if config.fcm_enabled and use_fcm:
            channels_to_send.append('fcm')
        if config.email_enabled and use_email:
            channels_to_send.append('email')
        if config.sms_enabled and use_sms:
            channels_to_send.append('sms')
        if config.whatsapp_enabled and use_whatsapp:
            channels_to_send.append('whatsapp')

        if not channels_to_send:
            logger.info(f"No active channels for template {template_slug}")
            return False

        results = []
        safe_context = _json_safe(context)
        for channel in channels_to_send:
            res = NotificationService.create_notification([user], title, body, channel, safe_context)
            results.append(res)
        
        return len(results) > 0

    @staticmethod
    def broadcast_announcement(title: str, body: str, channel: str = 'fcm', data: Optional[Dict[str, Any]] = None, created_by=None):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.filter(is_active=True)
        return NotificationService.create_notification(users, title, body, channel, data, created_by=created_by)
