import random
from twilio.rest import Client
from django.core.mail import send_mail
from django.conf import settings
import requests


class TermiiClient:
    BASE_URL = "https://api.ng.termii.com/api"

    def __init__(self, api_key: str, sender_id: str, email_configuration_id: str = None):
        self.api_key = api_key
        self.sender_id = sender_id
        self.email_configuration_id = email_configuration_id

    # -----------------------------------------
    # 1️⃣ Send OTP via SMS
    # -----------------------------------------
    def send_otp_sms(self, phone_number: str, message: str = "") -> dict:
        """
        Send OTP via SMS using Termii's token endpoint.
        - pin_attempts: number of tries allowed before expiry
        - pin_time_to_live: validity in minutes
        """
        url = f"{self.BASE_URL}/sms/send"

        if phone_number.startswith("+"):
            phone_number = phone_number[1:]

        payload = {
            "api_key": self.api_key,
            "to": phone_number,
            "from": self.sender_id,
            "type": "plain",
            "sms": message,
            "channel": "generic", 
        }

        response = requests.post(url, json=payload)
        print("SMS OTP res:", response)
        data = response.json()
        if not response.ok:
            raise Exception(f"OTP SMS failed: {data}")
        return data

    # -----------------------------------------
    # 2️⃣ Send OTP via WhatsApp
    # -----------------------------------------
    def send_otp_whatsapp(self, phone_number: str, message: str = "") -> dict:
        """
        Send OTP via WhatsApp using Termii's WhatsApp channel.
        """
        url = f"{self.BASE_URL}/sms/send"
        if phone_number.startswith("+"):
            phone_number = phone_number[1:]

        payload = {
        #    "channel": "whatsapp_otp",
            "api_key": self.api_key,
            "to": phone_number,
            "from": self.sender_id,
            "type": "plain",
            "sms": message,
            "channel": "whatsapp_otp",
        }

        response = requests.post(url, json=payload)
        print("WhatsApp res: ", response.content)
        data = response.json()
        if not response.ok:
            raise Exception(f"OTP WhatsApp failed: {data}")
        return data
    
    def send_otp_email(self, recipient_email: str, otp_code:  str):
        url = f"{self.BASE_URL}/email/otp/send"
        payload = {
                    "api_key" : self.api_key,
                    "email_address" : recipient_email,
                    "code": otp_code,
                    "email_configuration_id": self.email_configuration_id
            }
        headers = {
        'Content-Type': 'application/json',
        }
        response = requests.request("POST", url, headers=headers, json=payload)
        print(response.text)

    



def send_sms_otp(phone_number, message):
    """
    Send OTP via SMS using Twilio
    :param phone_number: Recipient phone number (+234.... format)
    :param otp: Generated OTP
    """

    if settings.DEBUG:
        phone_number = "+2348163351109"
    # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client = TermiiClient(settings.TERMII_API_KEY, settings.TERMII_SENDER_ID)

    res = client.send_otp_sms(
        phone_number=phone_number,
        message=message
    )
    return res


def send_whatsapp_otp(phone_number, message):
    """
    Send OTP via WhatsApp using Twilio
    :param phone_number: Recipient WhatsApp number (+234.... format)
    :param otp: Generated OTP
    """
    if settings.DEBUG:
        phone_number = "+2348082668519"

    client = TermiiClient(settings.TERMII_API_KEY, settings.TERMII_SENDER_ID)

    # message = client.messages.create(
    #     from_='whatsapp:+14155238886',
    #     content_sid='HX229f5a04fd0510ce1b071852155d3e75',
    #     content_variables='{"1":"'+ message +'"}',
    #     to='whatsapp:'+phone_number
    # )
    # message = client.messages.create(
    #     body=message,
    #     from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
    #     to=f"whatsapp:{phone_number}"
    # )


    res = client.send_otp_whatsapp(
        phone_number=phone_number,
        message=message
    )
    return res


def send_email_otp(email, otp):
    """
    Send OTP via Email (using Django's email backend)
    Requires EMAIL_BACKEND configured in settings.py
    """
    client = TermiiClient(settings.TERMII_API_KEY, settings.TERMII_SENDER_ID, settings.TERMII_EMAIL_CONFIG_ID)

    client.send_otp_email(email, otp)
    return True
