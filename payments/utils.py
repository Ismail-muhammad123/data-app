import requests
from django.conf import settings

#  = "https://seerbitapi.com/api/v2"  # or sandbox URL

def get_encrypted_key():
    payload = {"key": f"{settings.SEERBIT_SECRET_KEY}.{settings.SEERBIT_PUBLIC_KEY}"}
    response = requests.post(f"https://seerbitapi.com/api/v2/encrypt/keys", json=payload, headers={"Content-Type": "application/json"})
    data = response.json()

    if response.status_code == 200 and data.get("status") == "SUCCESS":
        return data["data"]["EncryptedSecKey"]["encryptedKey"]
    raise Exception("Failed to get encrypted key from SeerBit")
