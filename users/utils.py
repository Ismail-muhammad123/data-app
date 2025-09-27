import random
from datetime import timedelta
from django.utils import timezone
from config.utils import send_email_otp, send_sms_otp, send_whatsapp_otp
from users.models import OTP

def generate_otp():
    return str(random.randint(100000, 999999))

def otp_expiry():
    return timezone.now() + timedelta(minutes=5)


# def regidter_new_admin():
#     pass

# def register_new_customer():
#     pass


# def send_sms(phone_number, message):
#     print(f"SMS message '{message}' to {phone_number}")


# def send_whatsapp(phone_number, message):
#     print(f"WhatsApp message '{message}' to {phone_number}")


# def send_email(email_address, message_header, message_body):
#     print(f"Email headed '{message_header}' and body {message_body}  sent to {email_address}")



def send_otp_code(user, purpose, prefered_channel=None):
    otp = generate_otp()
    expiry = otp_expiry()

    # Save OTP and expiry to user (assuming user model has these fields)
    # user.otp_code = otp
    # user.otp_expiry = expiry
    # user.save()

    OTP.objects.create(
        user=user,
        code=otp,
        purpose=purpose, 
        expires_at=expiry,
    )

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

    phone = user.phone_number

    if phone[0] ==0:
        phone = phone[1:]
    
    phone = user.phone_country_code + phone

    for channel in channels:
        if channel == 'sms' and hasattr(user, 'phone_number') and phone:
            send_sms_otp(phone, message)
        elif channel == 'whatsapp' and hasattr(user, 'phone_number') and phone:
            send_whatsapp_otp(phone, message)
        elif channel == 'email' and hasattr(user, 'email') and user.email:
            send_email_otp(user.email, message, "OTP Code")