import random
import requests
import json
import logging
from django.conf import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ZohoService:
    @staticmethod
    def send_sms(phone_number: str, message: str) -> bool:
        """
        Sends SMS via Zoho SMS API.
        """
        api_key = getattr(settings, 'ZOHO_API_KEY', None)
        sender_id = getattr(settings, 'ZOHO_SMS_SENDER_ID', 'AStarData')

        if not api_key:
            logger.error("ZOHO_API_KEY not configured")
            return False

        # Clean phone number
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]

        try:
            # Note: Using Zoho SMS API v2 endpoint
            response = requests.post(
                "https://sms.zoho.com/api/v2/send",
                headers={
                    "Authorization": f"Zoho-enczapikey {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "to": phone_number,
                    "from": sender_id,
                    "message": message
                },
                timeout=15
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Zoho SMS error: {e}")
            return False

    @staticmethod
    def send_whatsapp(phone_number: str, message: str) -> bool:
        """
        Sends WhatsApp message via Zoho WhatsApp API.
        """
        api_key = getattr(settings, 'ZOHO_API_KEY', None)
        wa_number = getattr(settings, 'ZOHO_WHATSAPP_NUMBER', '')

        if not api_key:
            logger.error("ZOHO_API_KEY not configured")
            return False

        if phone_number.startswith('+'):
            phone_number = phone_number[1:]

        try:
            # Note: Zoho WhatsApp integration usually uses these parameters
            response = requests.post(
                "https://whatsapp.zoho.com/api/v1/send",
                headers={
                    "Authorization": f"Zoho-enczapikey {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "to": phone_number,
                    "from": wa_number,
                    "message": message
                },
                timeout=15
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Zoho WhatsApp error: {e}")
            return False

    @staticmethod
    def send_email_zepto(email: str, subject: str, html_content: str) -> bool:
        """
        Sends email via Zoho ZeptoMail API.
        """
        zepto_url = getattr(settings, 'ZOHO_MAIL_API_URL', "https://api.zeptomail.com/v1.1/email")
        api_key = getattr(settings, 'ZOHO_API_KEY', None)
        from_email = getattr(settings, 'ZOHO_EMAIL_USER', 'noreply@astardata.com')

        if not api_key:
            logger.error("ZOHO_API_KEY not configured for ZeptoMail")
            return False

        payload = {
            "from": {"address": from_email, "name": "A-Star Data"},
            "to": [
                {
                    "email_address": {
                        "address": email,
                        "name": email.split('@')[0]
                    }
                }
            ],
            "subject": subject,
            "htmlbody": html_content
        }

        try:
            response = requests.post(
                zepto_url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Zoho-enczapikey {api_key}"
                },
                json=payload,
                timeout=15
            )
            return response.status_code == 200 or response.status_code == 201
        except Exception as e:
            logger.error(f"ZeptoMail error: {e}")
            return False


def send_sms_otp(phone_number, message):
    """
    Send OTP via SMS using Zoho
    """
    print(f"DEBUG: Preparing to send Zoho SMS to {phone_number}")
    return ZohoService.send_sms(phone_number, message)


def send_whatsapp_otp(phone_number, message):
    """
    Send OTP via WhatsApp using Zoho
    """
    print(f"DEBUG: Preparing to send Zoho WhatsApp to {phone_number}")
    return ZohoService.send_whatsapp(phone_number, message)


def send_email_otp(email, otp):
    """
    Send OTP via Email using ZeptoMail
    """
    print(f"DEBUG: Preparing to send ZeptoMail OTP to {email}")
    subject = "Verification Code - A-Star Data"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Verification Code</h2>
        <p>Your verification code is: <strong>{otp}</strong></p>
        <p>This code will expire in 5 minutes.</p>
        <p>If you did not request this code, please ignore this email.</p>
    </div>
    """
    return ZohoService.send_email_zepto(email, subject, html_content)
