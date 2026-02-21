import random
from datetime import timedelta
from django.utils import timezone
from config.utils import send_email_otp, send_sms_otp, send_whatsapp_otp
from users.models import OTP

def generate_otp():
    return str(random.randint(100000, 999999))

def otp_expiry():
    return timezone.now() + timedelta(minutes=5)

def send_otp_code(user, purpose, preferred_channel=None):
    otp = generate_otp()
    expiry = otp_expiry()

    OTP.objects.create(
        user=user,
        code=otp,
        purpose=purpose, 
        expires_at=expiry,
        channel=preferred_channel
    )

    # Prepare message
    message = f"Your OTP for {purpose} is {otp}. It expires in 5 minutes."

    # Send OTP based on preferred channel
    channels = []
    print(user.email)
    if preferred_channel is None:
        channels = ['sms', 'whatsapp']
        if hasattr(user, 'email') and user.email and user.email.strip():
            print("User has valid email, adding 'email' to channels.")
            channels.append('email')
    else:
        channels = [preferred_channel]

    phone = user.phone_number

    if phone[0] is "0":
        phone = phone[1:]
    
    phone = user.phone_country_code + phone
    
    for channel in channels:
        if channel == 'sms' and hasattr(user, 'phone_number') and phone:
            send_sms_otp(phone, message)
        elif channel == 'whatsapp' and hasattr(user, 'phone_number') and phone:
            send_whatsapp_otp(phone, message)
        elif channel == 'email' and hasattr(user, 'email') and user.email:
            send_email_otp(user.email, otp)

