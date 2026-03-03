# A-Star Data App Backend

A robust Django-based backend for a utility and telecommunications application. Features include automated wallet systems, virtual account generation, and seamless integration with multiple service providers for Data, Airtime, Electricity, and Cable TV subscriptions.

---

## 🚀 Overview

This backend powers the **A-Star Data App**, providing a secure and scalable infrastructure for users to manage their wallets and purchase utility services. It integrates with major Nigerian payment gateways and service aggregators.

### Key Features
- **User Management**: Simple signup flow, JWT authentication, and secure PIN-based transactions.
- **Wallet System**: Real-time balance management, transaction history, and detailed auditing.
- **Virtual Accounts**: Automatic and manual generation of dedicated virtual accounts for instant wallet funding (via Paystack/Monnify).
- **Service Integration**: 
    - **Telecom**: Airtime and Data (MTN, Glo, Airtel, 9mobile) via ClubKonnect/VTPass.
    - **Utilities**: Electricity bills and Cable TV (DSTV, GOTV, Startimes).
- **Notifications**: OTP verification via SMS, Email, and WhatsApp using Termii.
- **Admin Dashboard**: Enhanced UI with custom KPI tracking and system configuration via Django Jazzmin.

---

## 📂 Project Structure

```text
backend/
├── config/             # Project settings, root URLs, and core utilities.
├── users/              # User models, OTP logic, and authentication endpoints.
├── wallet/             # Virtual accounts and wallet transaction processing.
├── payments/           # Paystack, Monnify, and external payment integrations.
├── orders/             # Logic for purchasing data, airtime, and utility bills.
├── summary/            # Admin dashboard aggregation and site config models.
├── static/             # Static assets (images, custom CSS/JS for admin).
├── manage.py           # Django management script.
└── .env                # Environment variables (Sensitive information).
```

---

## 🛠 Technology Stack

- **Framework**: [Django](https://www.djangoproject.com/) 5.2.x
- **API**: [Django REST Framework](https://www.django-rest-framework.org/) (DRF)
- **Database**: SQLite (Development) / PostgreSQL (Production ready via `dj-database-url`)
- **UI (Admin)**: [Jazzmin](https://github.com/farridav/django-jazzmin) (Custom Admin theme)
- **Documentation**: [DRF Spectacular](https://drf-spectacular.readthedocs.io/) (OpenAPI 3.0)
- **Key Libraries**:
    - `djangorestframework-simplejwt`: Token-based authentication.
    - `requests`: Handling external API communications.
    - `python-dotenv`: Environment configuration management.
    - `whitenoise`: Static file serving for production.

---

## 📥 Installation and Setup

### 1. Prerequisites
- Python 3.10+
- Virtualenv

### 2. Clone and Setup Environment
```bash
# Navigate to project directory
cd "Data App/backend"

# Create and activate virtual environment
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and populate it with your credentials:
```env
DEBUG=True
PRODUCTION=False
SECRET_KEY=your_django_secret_key

# Payment Gateways
PAYSTACK_SECRET_KEY=sk_test_...
TERMII_API_KEY=TL...
TERMII_SENDER_ID=AStarData

# Telecommunication APIs
CLUBKONNECT_USER_ID=...
CLUBKONNECT_API_KEY=...
```

### 4. Database Initialization
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 6. Run Server
```bash
python manage.py runserver
```

---

## 📖 API Documentation

The project includes an interactive API documentation interface:
- **Swagger UI**: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Schema (YAML)**: [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)

---

## ⚙ Maintenance and Scripts

- **Collect Static**: `python manage.py collectstatic --noinput`
- **Build Script**: Use `./build.sh` for deployment preparations.
- **Log Monitoring**: Logs are integrated into the Django admin for easy oversight of transaction failures.

---

## 📄 License
This project is proprietary. All rights reserved.
