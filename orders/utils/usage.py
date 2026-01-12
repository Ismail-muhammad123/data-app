from ebills_client import EBillsClient
import uuid
from pprint import pprint


client = EBillsClient()

# Authenticate
client.authenticate()

# Get balance
balance = client.get_balance()
pprint(balance)

# Get Data variations
variations = client.list_services()
print("Services:")
pprint(variations)



# # Get Data variations
# variations = client.get_data_variations()
# print("Data Variations:")
# pprint(variations)

# # Get MTN data plans
# plans = client.get_data_variations(service_id="mtn")
# pprint("MTN Data Plans: \n",plans)

# # Get GLO data plans
# plans = client.get_data_variations(service_id="glo")
# pprint("GLO Data Plans: \n",plans)

# # Get AIRTEL data plans
# plans = client.get_data_variations(service_id="airtel")
# print("AIRTEL Data Plans: \n",plans)




# # Buy airtime
# airtime_tx = client.buy_airtime(
#     request_id=str(uuid.uuid4()),
#     phone="08012345678",
#     service_id="mtn",
#     amount=100,
# )
# print(airtime_tx)

# # Buy data
# data_tx = client.buy_data(
#     request_id=str(uuid.uuid4()),
#     phone="08012345678",
#     service_id="mtn",
#     variation_id="354466",
# )
# print(data_tx)
