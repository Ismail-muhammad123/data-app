# # vtpass_integration/services.py

# import uuid
# from .utils import vtpass_post, vtpass_get

# def generate_request_id():
#     return str(uuid.uuid4())


# # 🔹 Airtime Purchase
# def buy_airtime(phone: str, amount: float, network: str):
#     """
#     network can be: 'mtn', 'glo', 'airtel', 'etisalat'
#     """
#     payload = {
#         "request_id": generate_request_id(),
#         "serviceID": network,
#         "amount": amount,
#         "phone": phone,
#     }
#     return vtpass_post("/api/pay", payload)


# # 🔹 Data Purchase
# def buy_data(phone: str, variation_code: str, network: str):
#     """
#     variation_code comes from VTpass API (bundle size e.g. '500MB', '1GB').
#     """
#     payload = {
#         "request_id": generate_request_id(),
#         "serviceID": network,  # e.g. "mtn-data", "glo-data"
#         "billersCode": phone,
#         "variation_code": variation_code,
#         "phone": phone,
#     }
#     return vtpass_post("/api/pay", payload)


# # 🔹 Smile Internet Purchase
# def buy_smile(account_number: str, variation_code: str, amount: float):
#     """
#     Smile internet requires account_number and bundle variation.
#     """
#     payload = {
#         "request_id": generate_request_id(),
#         "serviceID": "smile-direct",
#         "billersCode": account_number,
#         "variation_code": variation_code,
#         "amount": amount,
#         "phone": account_number,  # sometimes same as billersCode
#     }
#     return vtpass_post("/api/pay", payload)


# # 🔹 Get Data Plans
# def get_data_plans(network: str):
#     """
#     Get available data plans (variations) for a network.
#     """
#     return vtpass_get("/api/service-variations", {"serviceID": f"{network}-data"})
