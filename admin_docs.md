# Starboy Global Admin API Documentation (v2.0)

This document provides a highly structured overview of the administrative API endpoints. All endpoints are categorized for clarity in the Swagger UI.

## 👤 User Management (`Admin User Management`)
Handle retail customers, agents, and staff members.

- **List/Search Users**: `GET` `/api/admin/users/` (Supports search by phone, email, referral).
- **User Detail**: `GET` `/api/admin/users/{id}/`
- **Approve KYC**: `POST` `/api/admin/users/{id}/approve-kyc/`
    - Payload: `{"reason": "Document matches user details"}`
- **Reject KYC**: `POST` `/api/admin/users/{id}/reject-kyc/`
    - Payload: `{"reason": "Blurred ID card image"}`
- **Upgrade to Agent**: `POST` `/api/admin/users/{id}/upgrade-to-agent/`
    - Payload: `{"commission_rate": 5.5}`

---

## 💰 Finance & Wallets (`Admin Wallets` & `Admin Payments`)
Audit and manage the flow of funds within the system.

- **Wallet Audit Log**: `GET` `/api/admin/wallet/transactions/` (Filters: `user`, `type`, `initiator`).
- **Manual Adjustment**: `POST` `/api/admin/wallet/transactions/manual-adjustment/`
    - Payload: `{"user_id": 1, "amount": 500, "type": "credit/debit", "reason": "..."}`
- **Deposits Management**: `GET/PATCH` `/api/admin/payments/deposits/`
- **Withdrawals Management**: `GET/PATCH` `/api/admin/payments/withdrawals/`

---

## ⚡ VTU Operations (`Admin Purchases` & `Admin VTU Config`)
Full control over service fulfillment and vendor routing.

- **Purchase History**: `GET` `/api/admin/purchases/`
- **Manual Refund**: `POST` `/api/admin/purchases/{id}/refund/` (Credits user wallet and updates status).
- **Retry Purchase**: `POST` `/api/admin/purchases/{id}/retry/`
- **Provider Settings**: `GET/POST/PATCH` `/api/admin/vtu/providers/`
    - Manage API keys, `max_retries`, and `auto_refund` flags per vendor.
- **Service Routing**: `GET/POST/PATCH` `/api/admin/vtu/routings/`
    - Set primary and fallback providers for Airtime, Data, TV, etc.

---

## 🏷️ Pricing & Variations (`Admin Pricing & Plans`)
Manage tiered pricing for retail and agency users.

- **Data Variations**: `GET/POST/PATCH` `/api/admin/pricing/data/`
    - Set `selling_price` (retail) and `agent_price` (wholesale).
- **TV Variations**: `GET/POST/PATCH` `/api/admin/pricing/tv/`
- **Promo Codes**: `GET/POST/PATCH` `/api/admin/pricing/promos/`

---

## 🎟️ Support & Communication (`Admin Support`)
Advocate for your users by managing tickets and messages.

- **Support Overview**: `GET` `/api/admin/support/`
- **Admin Reply**: `POST` `/api/admin/support/{id}/reply/`
    - Payload: `{"message": "Hello, we are investigating..."}` (Auto-sets status to `in_progress`).

---

## 🏦 Administrative Transfers (`Admin Administrative Transfers`)
Securely move platform funds to vendors or external accounts.

- **Saved Beneficiaries**: `GET/POST/DELETE` `/api/admin/vtu/transfer/beneficiaries/`
- **Initiate Transfer (2FA)**: `POST` `/api/admin/transfer/initiate/`
    - Payload: `{"beneficiary_id": 1, "amount": 10000, "otp": "123456"}`
- **Transfer Audit**: `GET` `/api/admin/transfer/logs/`
