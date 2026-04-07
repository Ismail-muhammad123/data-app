# Implementation Plan: Google Sign-In, Dynamic VTU Providers & Public Developer API

## Overview

Three major features to build on top of the existing Django backend:

1. **Google Sign-In** — The endpoint already exists (`/api/account/google/`) and the `GoogleAuthView` + `google_id` field are in place. The focus is on completing the Flutter integration guide, fixing the `first_name`/`last_name` population from Google profile, and adding a guide doc.
2. **Dynamic VTU Provider Admin Console** — A new `DynamicVTUProvider` model in Django admin where admins can configure any API provider (request endpoints, methods, auth headers, response field mappings) without writing code.
3. **Public Developer API** — A `developer_api` app with API key authentication, account upgrade flow, and public endpoints for services, networks, packages, purchasing, and webhooks.

---

## User Review Required

> [!IMPORTANT]
> **Feature 1 (Google Sign-In)**: The `GoogleAuthView` is already 90% implemented. The main gap is that new users registered via Google don't get `first_name`/`last_name` set from the Google token. This plan fixes that + produces a complete Flutter guide. No new Python packages needed — `google-auth` is already installed.

> [!IMPORTANT]
> **Feature 2 (Dynamic VTU Providers)**: This adds a **new model `DynamicVTUProvider`** that allows configuring generic REST API providers entirely from Django admin — including per-operation URL, HTTP method, request params, and response field mappings. This does NOT replace existing hardcoded providers (VTPass, ClubKonnect, ArewaGlobal). It adds a new side-by-side system for quickly onboarding new providers without code changes. The `GenericLocalProvider` and `ProviderRouter` are extended to support it.

> [!WARNING]
> **Feature 3 (Public API)**: This requires a **new Django app** (`developer_api`) and will add an `is_developer` flag + `api_key` field to the `User` model (or a separate `DeveloperProfile` model — see Open Questions). All public API calls require `X-API-Key: <key>` header. Webhooks fire to the developer's registered webhook URL on purchase status changes.

> [!CAUTION]
> The `User` model currently uses `phone_number` as USERNAME_FIELD. Google sign-in creates users with a phone number that must be provided at sign-in time if the user is new. This is by design. The plan preserves this behavior.

---

## Proposed Changes

### Feature 1 — Google Sign-In Enhancement & Flutter Guide

---

#### [MODIFY] [auth.py](file:///home/hawkeye/Desktop/projects/Data%20App/backend/users/views/auth.py)

- Populate `first_name`, `last_name` from the Google `idinfo` payload when creating a new user.
- Return `is_new_user: true` in the response so Flutter can route new users to a profile completion screen.
- Handle the case where `given_name`/`family_name` may be absent.

---

#### [NEW] [GOOGLE_SIGNIN_FLUTTER_GUIDE.md](file:///home/hawkeye/Desktop/projects/Data%20App/backend/GOOGLE_SIGNIN_FLUTTER_GUIDE.md)

A comprehensive Flutter implementation guide covering:
- Google Cloud Console credentials needed (Web Client ID, Android SHA-1, iOS Bundle ID)
- Packages to add (`google_sign_in`, `http`)
- Step-by-step Flutter code (sign in, extract `idToken`, POST to backend)
- Handling `PHONE_NUMBER_REQUIRED` flow (new user needs to enter phone)
- Handling `requires_2fa` flow
- Token storage and authentication flow

**Credentials needed from Google Cloud Console:**

| Credential | Where to get it | Used in |
|---|---|---|
| `GOOGLE_CLIENT_ID` (Web OAuth 2.0) | APIs & Services → Credentials → Web Client | Django `settings.py` → `.env` |
| Android OAuth Client ID (with SHA-1) | APIs & Services → Credentials → Android | `google-services.json` in Flutter |
| iOS OAuth Client ID (with Bundle ID) | APIs & Services → Credentials → iOS | `GoogleService-Info.plist` in Flutter |
| `google-services.json` | Firebase Console (links to GCP project) | Flutter `android/app/` |
| `GoogleService-Info.plist` | Firebase Console (links to GCP project) | Flutter `ios/Runner/` |

---

### Feature 2 — Dynamic VTU Provider Admin Console

---

#### [NEW] `orders/models.py` additions — `DynamicVTUProvider` model

New model with these sections:

```python
class DynamicVTUProvider(models.Model):
    # Identity
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    
    # Auth / credentials
    base_url = models.URLField()
    auth_type = models.CharField(choices=[('header','Header'),('query','Query Param'),('basic','Basic Auth')])
    auth_key_name = models.CharField(max_length=100)   # e.g. "Authorization" or "api_key"
    auth_key_value = models.TextField()               # e.g. "Token abc123"
    extra_headers = models.JSONField(default=dict)    # {"Content-Type": "application/json"}

    # Enabled services bitmask / checkboxes
    supports_airtime = models.BooleanField(default=False)
    supports_data     = models.BooleanField(default=False)
    supports_tv       = models.BooleanField(default=False)
    supports_electricity = models.BooleanField(default=False)
    supports_internet = models.BooleanField(default=False)
    supports_education= models.BooleanField(default=False)
```

#### [NEW] `DynamicOperationConfig` model (inline in admin)

For each operation (get_networks, get_packages, buy, verify, query), a row with:

```python
class DynamicOperationConfig(models.Model):
    OPERATION_CHOICES = [
        ('get_networks', 'Get Networks'),
        ('get_packages', 'Get Packages/Variations'),
        ('purchase',     'Purchase'),
        ('verify',       'Verify/Query Status'),
        ('validate_meter','Validate Meter'),
        ('validate_card', 'Validate Smart Card'),
        ('get_balance',  'Get Wallet Balance'),
    ]
    provider = models.ForeignKey(DynamicVTUProvider, related_name='operations')
    service_type = models.CharField(choices=SERVICE_CHOICES)  # airtime/data/tv/electricity…
    operation_type = models.CharField(choices=OPERATION_CHOICES)
    
    # Request config
    endpoint = models.CharField(max_length=500)    # e.g. "/api/v1/data/plans"
    http_method = models.CharField(choices=[('GET','GET'),('POST','POST')])
    request_params = models.JSONField(default=dict) # static params always sent
    # Field mapping: maps our internal param names → provider's param names
    # e.g. {"phone": "mobile_number", "network": "network_id", "plan_id": "plan"}
    field_mapping = models.JSONField(default=dict)
    
    # Response mapping
    # Maps provider response fields → our standard fields
    # e.g. {"status_field": "Status", "success_value": "successful", "token_field": "token"}
    response_mapping = models.JSONField(default=dict)
```

#### [NEW] `orders/providers/dynamic.py`

A `DynamicProvider` class that:
- Takes a `DynamicVTUProvider` model instance
- Reads `DynamicOperationConfig` rows for each operation
- Builds and fires HTTP requests dynamically
- Maps responses back to our standard `{'status': 'SUCCESS', ...}` format
- Implements all `BaseVTUProvider` abstract methods

#### [MODIFY] [router.py](file:///home/hawkeye/Desktop/projects/Data App/backend/orders/router.py)

- Add dynamic provider lookup: if a provider name is not in `FACTORIES`, check if a `DynamicVTUProvider` with that name exists and instantiate `DynamicProvider(instance)`.
- `ProviderRouter.get_provider_implementation()` tries hardcoded factories first, then dynamic lookup.

#### [MODIFY] [orders/admin.py](file:///home/hawkeye/Desktop/projects/Data App/backend/orders/admin.py)

- Register `DynamicVTUProvider` with `DynamicOperationConfig` as `TabularInline`.
- Add JSON field help text and a "Test Connection" admin action that fires `get_balance`.
- Add a "Sync from Provider" action per service type.

#### [MODIFY] [orders/models.py](file:///home/hawkeye/Desktop/projects/Data App/backend/orders/models.py)

- `VTUProviderConfig.PROVIDER_CHOICES` currently comes from `registry.py`. Update `ProviderRouter` to also list active `DynamicVTUProvider` names dynamically.
- Alternatively, `DynamicVTUProvider` is a completely separate model from `VTUProviderConfig`.

> [!NOTE]
> **Design Decision**: `DynamicVTUProvider` is separate from `VTUProviderConfig` to avoid breaking existing migrations and provider logic. `ServiceRouting` can reference either type. The `ProviderRouter` checks both.

---

### Feature 3 — Public Developer API

---

#### [NEW] Django app: `developer_api/`

New app with the following structure:
```
developer_api/
  __init__.py
  apps.py
  models.py          # DeveloperProfile, APIKey, WebhookEndpoint, APIRequestLog
  authentication.py  # APIKeyAuthentication class
  permissions.py     # IsActiveDeveloper permission
  serializers.py
  views/
    __init__.py
    auth.py          # upgrade to developer, get/regenerate API key
    services.py      # list services, networks, packages
    purchase.py      # make purchase, check status
    webhook.py       # register/update webhook URL
  urls.py
  admin.py
```

#### Models

```python
class DeveloperProfile(models.Model):
    user = models.OneToOneField(User, related_name='developer_profile')
    is_active = models.BooleanField(default=False)
    upgraded_at = models.DateTimeField(null=True)
    upgraded_by = models.ForeignKey(User, ...)  # admin who approved
    company_name = models.CharField(...)
    website = models.URLField(...)
    reason = models.TextField()   # why they want API access
    
class APIKey(models.Model):
    developer = models.OneToOneField(DeveloperProfile, related_name='api_key')
    key = models.CharField(max_length=64, unique=True)  # generated: "sk_live_xxxxx"
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    daily_limit = models.PositiveIntegerField(default=1000)
    monthly_limit = models.PositiveIntegerField(default=30000)

class WebhookEndpoint(models.Model):
    developer = models.ForeignKey(DeveloperProfile, related_name='webhooks')
    url = models.URLField()
    secret = models.CharField(max_length=64)  # for HMAC signature
    events = models.JSONField(default=list)   # ['purchase.success', 'purchase.failed']
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class APIRequestLog(models.Model):
    developer = models.ForeignKey(DeveloperProfile)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Authentication

Custom `APIKeyAuthentication` class that:
- Reads `X-API-Key` header
- Looks up `APIKey` model, verifies `is_active`, checks rate limits
- Returns `(developer_profile.user, api_key)` as auth tuple
- Logs the request to `APIRequestLog`

#### Public API Endpoints (`/api/v1/`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/developer/register/` | Submit developer upgrade request |
| GET | `/api/v1/developer/profile/` | Get developer profile + API key status |
| POST | `/api/v1/developer/api-key/regenerate/` | Regenerate API key |
| GET/POST/PUT/DELETE | `/api/v1/developer/webhooks/` | Manage webhook endpoints |
| GET | `/api/v1/services/` | List all available service types |
| GET | `/api/v1/services/{service_type}/networks/` | List networks for a service (e.g. data → MTN, GLO) |
| GET | `/api/v1/services/{service_type}/networks/{network_id}/packages/` | List packages/variations |
| POST | `/api/v1/purchase/` | Make a purchase |
| GET | `/api/v1/purchase/{reference}/` | Check purchase status |
| POST | `/api/v1/verify/meter/` | Validate electricity meter |
| POST | `/api/v1/verify/smartcard/` | Validate TV smart card |

#### Purchase Webhook

When a `Purchase` changes status (success/failed), fire a `POST` to all active webhook URLs of the developer who initiated the purchase. Payload signed with HMAC-SHA256 using the webhook secret:

```json
{
  "event": "purchase.success",
  "reference": "REF_XXX",
  "service": "data",
  "amount": 500.00,
  "beneficiary": "08012345678",
  "status": "success",
  "timestamp": "2026-04-07T12:00:00Z"
}
```

Header: `X-Webhook-Signature: sha256=<hmac>`

#### [MODIFY] [orders/models.py](file:///home/hawkeye/Desktop/projects/Data App/backend/orders/models.py)

Add `initiated_via_api = models.BooleanField(default=False)` and `api_developer = models.ForeignKey(DeveloperProfile, null=True)` to `Purchase` model.

#### [MODIFY] [config/settings.py](file:///home/hawkeye/Desktop/projects/Data App/backend/config/settings.py)

- Add `developer_api` to `INSTALLED_APPS`
- Add `API_KEY_PREFIX = 'sk_live_'`
- Add `WEBHOOK_TIMEOUT = 5`

#### [MODIFY] [config/urls.py](file:///home/hawkeye/Desktop/projects/Data App/backend/config/urls.py)

Add `path('api/v1/', include('developer_api.urls'))`.

#### [MODIFY] Admin (`developer_api/admin.py`)

- `DeveloperProfile` admin with approve/revoke actions
- `APIKey` list with key rotation action
- `APIRequestLog` read-only with filters

---

## Open Questions

> [!IMPORTANT]
> **Q1**: Should the Developer API use a **separate `DeveloperProfile` model** (linked to existing users) or should we add `is_developer` + `api_key` fields directly to the `User` model? The plan proposes a separate model to keep concerns isolated. ✅ Separate model recommended.

> [!IMPORTANT]
> **Q2**: Should developer accounts require **admin approval** before their API key is activated, or should it be automatically granted upon request? Current plan assumes **manual admin approval** (admin checks `is_active=True` on `DeveloperProfile` in admin).

> [!IMPORTANT]
> **Q3**: For the **Dynamic VTU Provider**, should the admin be able to test a provider connection (fire a test request) directly from the Django admin? Plan includes a "Test Connection" admin action — confirm if needed.

> [!NOTE]
> **Q4**: Should the Developer API have **sandbox/test mode**? This could redirect test purchases to a mock response without hitting real provider APIs. Not in scope for v1 unless you want it.

> [!NOTE]
> **Q5**: Should the `DynamicVTUProvider` also be registerable in `ServiceRouting` (so it can be used as primary/fallback)? The current plan makes it interchangeable with `VTUProviderConfig` at the router level.

---

## Verification Plan

### Automated Tests
- Run `python manage.py check` after each migration
- Run `python manage.py makemigrations --check` to verify no missing migrations

### Manual Verification
1. **Google Sign-In**: Test the `/api/account/google/` endpoint with a real Firebase ID token. Verify first/last name saved.
2. **Dynamic Provider Admin**: Create a `DynamicVTUProvider` in admin with an Alrahuz-style config, fire a "Get Networks" operation.
3. **Developer API**: Create a test developer account, get an API key, hit `/api/v1/services/`, make a purchase, verify webhook fires.

### Swagger Docs
- All endpoints tagged under `Developer API` section in Swagger.
- API Key auth documented as `SecurityScheme` in `SPECTACULAR_SETTINGS`.
