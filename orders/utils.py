import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
import logging

from orders.models import DataPlan, DataNetwork

logger = logging.getLogger(__name__)

VTPASS_BASE_URL = getattr(settings, "VTPASS_BASE_URL") or "https://sandbox.vtpass.com/api"  # Change to live when ready
# VTPASS_USERNAME = getattr(settings, "VTPASS_USERNAME", "")
# VTPASS_PASSWORD = getattr(settings, "VTPASS_PASSWORD", "")

VTPASS_API_KEY = getattr(settings, "VTPASS_API_KEY", "")
VTPASS_API_SECRET = getattr(settings, "VTPASS_API_SECRET", "")
VTPASS_API_PUBLIC_KEY = getattr(settings, "VTPASS_API_PUBLIC_KEY", "")


# def get_auth_header():
#     """
#     VTPass uses Basic Auth (username:password).
#     """
#     from base64 import b64encode

#     # token = f"{VTPASS_USERNAME}:{VTPASS_PASSWORD}"
#     encoded = b64encode(token.encode()).decode()
#     return {"Authorization": f"Basic {encoded}"}


def get_api_auth_header(methosd="POST"):
    """
    VTPass uses API Key and Secret for some endpoints.
    """
    h = {"api-key": VTPASS_API_KEY}
    if methosd == "POST":
        h['secret-key'] = VTPASS_API_SECRET
    else:
        h['public-key'] = VTPASS_API_PUBLIC_KEY
    
    return h

def buy_data_plan(service_id, phone_number, amount, request_id, variation_code):
    """
    Purchase Airtime, Data, or Smile plan.
    Docs: https://vtpass.com/documentation
    """
    url = f"{VTPASS_BASE_URL}/pay"
    payload = {
        "serviceID": service_id,   # e.g., "mtn-data", "glo-airtime", "smile-direct"
        "phone": phone_number,
        "amount": str(amount),
        "billersCode": phone_number,  # for data plans, this is usually the same as phone number
        "request_id": request_id,  # must be unique
        "variation_code": variation_code,  # optional, depending on service
    }

    try:
        resp = requests.post(url, json=payload, headers=get_api_auth_header("POST"), timeout=30)
        return resp.json()
    except Exception as e:
        return {"error": str(e), "code": "999"}


def verify_transaction(request_id):
    """
    Verify transaction status from VTPass.
    """
    url = f"{VTPASS_BASE_URL}/requery"
    payload = {"request_id": request_id}

    try:
        resp = requests.post(url, json=payload, headers=get_api_auth_header("POST"), timeout=30)
        return resp.json()
    except Exception as e:
        return {"error": str(e), "code": "999"}
    

def buy_airtime(request_id, service_id, amount, beneficiary):
    url = f"{VTPASS_BASE_URL}/pay"
    payload = {
        "serviceID": service_id,  
        "request_id": request_id,  
        "phone": beneficiary,
        "amount": amount,
    }

    try:
        response = requests.post(url, json=payload, headers=get_api_auth_header("POST"), timeout=30)
        return response.json()
    except Exception as e:
        return {"error": str(e), "code": "999"}
