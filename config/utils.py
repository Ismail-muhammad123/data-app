import random
from twilio.rest import Client
from django.core.mail import send_mail
from django.conf import settings




# def generate_otp(length=6):
#     """Generate a numeric OTP"""
#     return str(random.randint(10**(length-1), (10**length)-1))


def send_sms_otp(phone_number, message):
    """
    Send OTP via SMS using Twilio
    :param phone_number: Recipient phone number (+234.... format)
    :param otp: Generated OTP
    """

    if settings.DEBUG:
        phone_number = "+2348163351109"
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        body=message,
        from_=settings.TWILIO_SMS_NUMBER,
        to=phone_number
    )
    return message.sid


def send_whatsapp_otp(phone_number, message):
    """
    Send OTP via WhatsApp using Twilio
    :param phone_number: Recipient WhatsApp number (+234.... format)
    :param otp: Generated OTP
    """
    if settings.DEBUG:
        phone_number = "+2348082668519"

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        from_='whatsapp:+14155238886',
        content_sid='HX229f5a04fd0510ce1b071852155d3e75',
        content_variables='{"1":"'+ message +'"}',
        to='whatsapp:'+phone_number
    )
    # message = client.messages.create(
    #     body=message,
    #     from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
    #     to=f"whatsapp:{phone_number}"
    # )
    return message.sid


def send_email_otp(email, message, subject="Your OTP Code"):
    """
    Send OTP via Email (using Django's email backend)
    Requires EMAIL_BACKEND configured in settings.py
    """
    message = message

    send_mail(
        subject,
        message,
        settings.TWILIO_EMAIL,  # or DEFAULT_FROM_EMAIL
        [email],
        fail_silently=False,
    )
    return True
