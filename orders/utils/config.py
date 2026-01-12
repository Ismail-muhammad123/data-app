import os

E_BILLS_BASE_URL = os.getenv("EBILLS_BASE_URL")
E_BILLS_USERNAME = os.getenv("EBILLS_USERNAME")
E_BILLS_PASSWORD = os.getenv("EBILLS_PASSWORD")
E_BILLS_TIMEOUT = int(os.getenv("EBILLS_TIMEOUT", 30))

# if not all([EBILLS_BASE_URL, EBILLS_USERNAME, EBILLS_PASSWORD]):
#     raise EnvironmentError("Missing required EBILLS environment variables")



# EBILLS_BASE_URL="https://ebills.africa/wp-json"
# EBILLS_USERNAME="ismaeelmuhammad123@gmail.com"
# EBILLS_PASSWORD="ismail_muhammad2020"
# EBILLS_TIMEOUT=30
