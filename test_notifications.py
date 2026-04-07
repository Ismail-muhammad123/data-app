import os
import sys
import django

# Setup path and Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from config.utils import send_sms_otp, send_whatsapp_otp, send_email_otp

def test_notifications():
    print("\n" + "="*40)
    print(" STARBOY GLOBAL NOTIFICATION TESTER ")
    print("="*40)
    print(f"DEBUG MODE: {settings.DEBUG}")
    
    # 1. Test SMS
    print("\n[1] Triggering SMS via Twilio...")
    # In debug mode, this will be redirected to +17405308370
    sms_res = send_sms_otp("+2348163351109", "Test Starboy SMS OTP: 123456")
    print(f"SMS Result: {'SUCCESS' if sms_res else 'FAILED'}")

    # 2. Test WhatsApp
    print("\n[2] Triggering WhatsApp via Twilio...")
    # In debug mode, this will be redirected to +17405308370
    wa_res = send_whatsapp_otp("+2348163351109", "Your Starboy OTP is 409173")
    print(f"WhatsApp Result: {'SUCCESS' if wa_res else 'FAILED'}")

    # 3. Test Email
    print("\n[3] Triggering Email via SendGrid...")
    email_res = send_email_otp("ismaeelmuhammad123@gmail.com", "998877")
    print(f"Email Result: {'SUCCESS' if email_res else 'FAILED'}")
    
    print("\n" + "="*40)
    print(" TEST COMPLETED ")
    print("="*40)

if __name__ == "__main__":
    test_notifications()
