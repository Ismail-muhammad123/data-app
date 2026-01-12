from orders.utils.ebills_client import EBillsClient


def get_api_wallet_balance():

    client = EBillsClient()

    client.authenticate()

    balance = client.get_balance()
    print("API Wallet Balance:", balance)

    if balance.get("code") == "success":
        print(balance['data'])
        currency = balance.get("data", {}).get("currency", "NGN")
        balance_amount = balance.get("data", {}).get("balance", 0)
        balance_amount = float(balance_amount)
        return f"{currency} {balance_amount:,.2f}"
