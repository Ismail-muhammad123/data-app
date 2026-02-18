from orders.services.clubkonnect import ClubKonnectClient


def get_api_wallet_balance():

    client = ClubKonnectClient()

    balance = client.get_balance()
    print("API Wallet Balance:", balance)

    if balance and isinstance(balance, dict):
        balance_amount = balance.get("balance", 0)
        try:
            balance_amount = float(balance_amount)
        except (TypeError, ValueError):
            balance_amount = 0.0
        return f"NGN {balance_amount:,.2f}"
    
    return "NGN 0.00"
