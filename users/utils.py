import random
from datetime import timedelta
from django.utils import timezone

def generate_otp():
    return str(random.randint(100000, 999999))

def otp_expiry():
    return timezone.now() + timedelta(minutes=5)


def regidter_new_admin():
    pass

def register_new_customer():
    pass


def send_sms(phone_number, message):
    print(f"SMS message '{message}' to {phone_number}")


def send_whatsapp(phone_number, message):
    print(f"WhatsApp message '{message}' to {phone_number}")


def send_email(email_address, message_header, message_body):
    print(f"Email headed '{message_header}' and body {message_body}  sent to {email_address}")



def send_otp_code(user, purpose, prefered_channel=None):
    otp = generate_otp()
    expiry = otp_expiry()

    # Save OTP and expiry to user (assuming user model has these fields)
    user.otp_code = otp
    user.otp_expiry = expiry
    user.save()

    # Prepare message
    message = f"Your OTP for {purpose} is {otp}. It expires in 5 minutes."

    # Send OTP based on preferred channel
    channels = []
    if prefered_channel is None:
        channels = ['sms', 'whatsapp']
        # if hasattr(user, 'email') and user.email:
        #     channels.append('email')
    else:
        channels = [prefered_channel]

    for channel in channels:
        if channel == 'sms' and hasattr(user, 'phone_number') and user.phone_number:
            send_sms(user.phone_number, message)
        elif channel == 'whatsapp' and hasattr(user, 'phone_number') and user.phone_number:
            send_whatsapp(user.phone_number, message)
        elif channel == 'email' and hasattr(user, 'email') and user.email:
            send_email(user.email, "OTP Code", message)