# 🌌 Starboy Global | Back-end Feature Checklist

This checklist tracks the implementation status of all core modules and features within the Starboy Global VTU platform.

## 👤 1. User Management & KYC
- [x] **Custom User Model**: Primary authentication via phone number.
- [x] **Role-Based Access Control (RBAC)**: Supports `customer`, `agent`, `staff`, and `superuser`.
- [x] **Comprehensive KYC Suite**:
    - [x] BVN/NIN storage and status tracking.
    - [x] Local ID card and face verification URL support.
    - [x] Admin manual verification endpoints.
- [x] **Agent Tiering**:
    - [x] Role-specific pricing (Standard vs. Agency rates).
    - [x] Agent commission tracking.
- [x] **Security**:
    - [x] 4-digit Transaction PIN for all debits and transfers.
    - [x] 2FA (TOTP/Google Authenticator) for administrative actions.

## 💰 2. Wallet & Financial Infrastructure
- [x] **Wallet Core**: Sub-module for instant balance tracking.
- [x] **Automated Crediting**:
    - [x] Paystack, Monnify, and Flutterwave integration.
    - [x] Dynamic bank account allocation for deposits.
- [x] **Withdrawal System**:
    - [x] Global withdrawal toggle (Admin).
    - [x] User withdrawal to local banks with automated processing.
- [x] **Admin Adjustments**: Manual credit/debit with reason logging.
- [x] **Audit Logs**: Categorized transaction history (`credit`, `debit`, `reversal`, `deposit`).

## ⚡ 3. VTU & Utility Services
- [x] **Airtime Distribution**: Top-up for all Nigerian networks (MTN, GLO, AIRTEL, 9MOBILE).
- [x] **Data Bundles**: Support for SME and Direct/Gifting variations.
- [x] **Pay TV**: Cable subscriptions (DSTV, GOTV, Startimes).
- [x] **Electricity**: Prepaid/Postpaid token generation for all DisCos (IKEDC, EKEDC, etc.).
- [x] **Educational PINs**: Exam pin purchases (WAEC, NECO, JAMB).
- [x] **Internet & Internet**: specialized broadband top-ups.

## 🌉 4. Provider Routing & Failover
- [x] **Generic Provider Interface**: Standardized 14+ VTU APIs (ClubKonnect, VTPass, HQDATA, etc.).
- [x] **Smart Router**: Centralized execution logic for all purchase types.
- [x] **Automatic Fallback**: Multi-provider support per service; moves to next provider on failure.
- [x] **Smart Retries**: Configurable retry counts per service variation.
- [x] **Auto-Refund**: Instant wallet reversal if all provider retries fail.

## 🛠️ 5. Administrative Controls (Admin API)
- [x] **Dashboard Analytics**: Success rates, daily sales, and financial summaries.
- [x] **User Moderation**: View all users, verify KYC, or suspend accounts.
- [x] **Pricing Engine**: Manage `selling_price` and `agent_price` for 100+ variations.
- [x] **Provider Configuration**: Hot-swap API credentials and toggle vendor status globally.
- [x] **Transfer Dashboard**: Securely move platform funds to saved beneficiaries (2FA protected).
- [x] **Categorized Swagger**: Staff-only endpoints organized by functional tags.

## 📢 6. Support & Advocacy
- [x] **Ticketing System**: Categorized user support requests (Transaction, Wallet, Account).
- [x] **Staff Response**: Threaded message replies between admin and user.
- [x] **Notifications**:
    - [x] Firebase Cloud Messaging (FCM) for push notifications.
    - [x] Global system announcements for maintenance or updates.

## 🛡️ 7. API Security & Documentation
- [x] **Mobile API Docs**: Comprehensive guide for frontend mobile app developers.
- [x] **Staff API Docs**: Detailed manual for administrative dashboard development.
- [x] **Rate Limiting**: Throttling on sensitive endpoints (Login, Reset PIN).
- [x] **Reference Generation**: LAGOS-tz based unique request IDs for all transactions.

---

### ✅ Deployment Readiness
- [x] Database Migrations applied.
- [x] Provider Fallback Registry populated.
- [x] Core Purchase Logic unit-tested in sandbox mode.
