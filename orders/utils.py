# vtpass_integration/utils.py

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

# VT_BASE = settings.VTPASS["BASE_URL"]
# VT_USERNAME = settings.VTPASS["USERNAME"]
# VT_PASSWORD = settings.VTPASS["PASSWORD"]


# def _auth():
#     return HTTPBasicAuth(VT_USERNAME, VT_PASSWORD)


# def vtpass_post(endpoint, payload):
#     url = f"{VT_BASE}{endpoint}"
#     headers = {"Content-Type": "application/json"}
#     resp = requests.post(url, json=payload, headers=headers, auth=_auth())
#     resp.raise_for_status()
#     return resp.json()


# def vtpass_get(endpoint, params=None):
#     url = f"{VT_BASE}{endpoint}"
#     headers = {"Content-Type": "application/json"}
#     resp = requests.get(url, params=params, headers=headers, auth=_auth())
#     resp.raise_for_status()
#     return resp.json()



VTPASS_BASE_URL = "https://sandbox.vtpass.com/api"  # Change to live when ready
VTPASS_USERNAME = getattr(settings, "VTPASS_USERNAME", "")
VTPASS_PASSWORD = getattr(settings, "VTPASS_PASSWORD", "")


def get_auth_header():
    """
    VTPass uses Basic Auth (username:password).
    """
    from base64 import b64encode

    token = f"{VTPASS_USERNAME}:{VTPASS_PASSWORD}"
    encoded = b64encode(token.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def purchase_service(service_id, phone_number, amount, request_id):
    """
    Purchase Airtime, Data, or Smile plan.
    Docs: https://vtpass.com/documentation
    """
    url = f"{VTPASS_BASE_URL}/pay"
    payload = {
        "serviceID": service_id,   # e.g., "mtn-data", "glo-airtime", "smile-direct"
        "phone": phone_number,
        "amount": str(amount),
        "request_id": request_id,  # must be unique
    }

    try:
        resp = requests.post(url, json=payload, headers=get_auth_header(), timeout=30)
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
        resp = requests.post(url, json=payload, headers=get_auth_header(), timeout=30)
        return resp.json()
    except Exception as e:
        return {"error": str(e), "code": "999"}