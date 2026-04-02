# Starboy Global Mobile API Documentation

This document defines the endpoints used by the mobile application for users and agents. 

## 1. User & Account Management
### Authentication
- **Signup**: `POST` `/api/account/signup/`
- **Activation**: `POST` `/api/account/activate-account/`
- **Login**: `POST` `/api/account/login/`
- **PIN Change**: `POST` `/api/account/change-pin/`
- **Password Reset**: `POST` `/api/account/reset-password/`
- **Logout**: `POST` `/api/account/logout/`

### Profile & Security
- **Profile Summary**: `GET` `/api/account/profile/`
- **FCM Registration**: `POST` `/api/account/register-fcm-token/`
- **Transaction PIN Setup**: `POST` `/api/account/set-transaction-pin/`
- **Transaction PIN Reset**: `POST` `/api/account/request-transaction-pin-reset/` (sends OTP) -> `POST` `/api/account/reset-transaction-pin/`

---

## 2. Wallet & Financial Operations
### Balance & History
- **Wallet Details**: `GET` `/api/wallet/`
- **Transaction History**: `GET` `/api/wallet/transactions/`
- **Transaction Detail**: `GET` `/api/wallet/transactions/{pk}/`

### Funding & Deposits
- **Init Deposit**: `POST` `/api/wallet/deposit/` -> Returns `checkout_url`.
- **Virtual Account Info**: `GET` `/api/wallet/virtual-account/` (for Monnify/Paystack dedicated accounts).

### Payouts & Transfers
- **Wallet-to-Wallet**: `POST` `/api/wallet/transfer/` (requires `transaction_pin`).
- **Withdrawal Request**: `POST` `/api/payment/withdrawal-request/` (requires `transaction_pin`).
- **Beneficiary Management**: `GET/POST` `/api/account/beneficiaries/`

---

## 3. VTU & Bill Payments
### Airtime & Data
- **List Networks**: `GET` `/api/orders/airtime-networks/`
- **List Data Plans**: `GET` `/api/orders/data-plans/?service_id={network_id}`
- **Buy Airtime**: `POST` `/api/orders/buy-airtime/`
- **Buy Data**: `POST` `/api/orders/buy-data/`

### Electricity & Cable
- **Verify Customer**: `POST` `/api/orders/verify-customer/` (Args: `service_id`, `customer_id`, `purchase_type`).
- **Buy Electricity**: `POST` `/api/orders/buy-electricity/`
- **Buy TV Sub**: `POST` `/api/orders/buy-tv-subscription/`

### Internet & Education
- **Buy Internet**: `POST` `/api/orders/buy-internet-subscription/`
- **Buy Education Pin**: `POST` `/api/orders/buy-education/` (WAEC/NECO).

### Order Utilities
- **Order History**: `GET` `/api/orders/purchase-history/`
- **Status Query**: `GET` `/api/orders/purchase-status/{pk}/` (Trigger manual check & potential refund).

---

## 4. Referrals & Rewards
- **Referral List**: `GET` `/api/account/referrals/`
- **Referral Stats**: `GET` `/api/account/referral-stats/`

---

## 5. Support & Feedback
- **Create Ticket**: `POST` `/api/support/`
- **List Tickets**: `GET` `/api/support/`
- **Ticket Chat**: `POST` `/api/support/{ticket_id}/messages/`
