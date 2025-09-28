import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
import logging

from orders.models import DataPlan, DataNetwork

logger = logging.getLogger(__name__)

# VTPASS_BASE_URL = settings.VTPASS.get("BASE_URL", "https://sandbox.vtpass.com")
# VT_USERNAME = settings.VTPASS["USERNAME"]
# VT_PASSWORD = settings.VTPASS["PASSWORD"]



# VTPASS_BASE_URL = settings.VTPASS["BASE_URL"]
# VT_USERNAME = settings.VTPASS["USERNAME"]
# VT_PASSWORD = settings.VTPASS["PASSWORD"]


# def _auth():
#     return HTTPBasicAuth(VT_USERNAME, VT_PASSWORD)


# def vtpass_post(endpoint, payload):
#     url = f"{VTPASS_BASE_URL}{endpoint}"
#     headers = {"Content-Type": "application/json"}
#     resp = requests.post(url, json=payload, headers=headers, auth=_auth())
#     resp.raise_for_status()
#     return resp.json()


# def vtpass_get(endpoint, params=None):
#     url = f"{VTPASS_BASE_URL}{endpoint}"
#     headers = {"Content-Type": "application/json"}
#     resp = requests.get(url, params=params, headers=headers, auth=_auth())
#     resp.raise_for_status()
#     return resp.json()



VTPASS_BASE_URL = "https://sandbox.vtpass.com/api"  # Change to live when ready
VTPASS_USERNAME = getattr(settings, "VTPASS_USERNAME", "")
VTPASS_PASSWORD = getattr(settings, "VTPASS_PASSWORD", "")


def generate_request_id():
    pass

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
    




# def get_service_variations(service_id: str):
#     """
#     Fetch variation list for a single service.
#     Endpoint used by many VTpass docs: /api/service-variations?serviceID=<service_id>
#     Returns JSON - inspect the shape (this code expects 'variations' or 'response' keys).
#     """
#     params = {"serviceID": service_id}
#     # Example response shapes:
#     # 1) {"response": {"variations": [ { "variation_code": "...", "name": "...", "amount": "..." }, ... ]}}
#     # 2) {"variations": [ ... ]}
#     # Normalize depending on actual API response:
#     # Try to find variations in common keys:

   

#     variations = None
#     if isinstance(resp, dict):
#         # common possible locations
#         variations = resp.get("variations") or resp.get("response", {}).get("variations") or resp.get("responseBody", {}).get("variations")
#     if variations is None:
#         # log raw response for debugging
#         logger.debug("Unexpected VTpass variations response for %s: %s", service_id, resp)
#         raise ValueError(f"Could not parse variations for service {service_id}")

#     return variations



# # 1. Get Services

#     # 2. Get Service Ids

#         # 3. Get variations

#             # 4. Save each variantion 
