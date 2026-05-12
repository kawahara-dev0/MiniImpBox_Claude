# Basic Design — Mini Improvement Box v1

## Metadata

| Field | Value |
|---|---|
| Status | Approved |
| Version | v1 |
| Created | 2026-05-11 |
| Author | AI Designer (Claude, Cowork mode) |
| Approver | System Owner (human) — 2026-05-11 |
| Requirements basis | docs/requirements/requirements-v1.md (Approved 2026-05-11) |
| ADRs basis | ADR-001 through ADR-006 (All Accepted 2026-05-11) |
| Policies checked | AGENTS.md, DESIGN_WORKFLOW.md, REVIEW_POLICY.md, SECURITY_POLICY.md, BASIC_DESIGN_CHECKLIST.md |

---

## 1. System Overview

Mini Improvement Box v1 is a Django 5.x web application running in Docker Compose. It exposes two distinct surfaces:

- **Public surface**: A single proposal submission form. No authentication required. Accessible to anyone who can reach the host.
- **Admin surface**: A password-protected portal for viewing and managing proposals. Accessible to authenticated administrators only.

```
[Browser]
   │
   ├── GET/POST /            → Proposal submission (public)
   ├── GET /submit/complete/ → Submission confirmation (public)
   │
   ├── GET/POST /admin-portal/login/           → Admin login
   ├── POST     /admin-portal/logout/          → Admin logout
   ├── GET      /admin-portal/                 → Proposal list (admin only)
   ├── GET      /admin-portal/proposals/<pk>/  → Proposal detail (admin only)
   └── POST     /admin-portal/proposals/<pk>/status/ → Status change (admin only)

[Django app container] ──── [PostgreSQL container]
                                     │
                              pgdata (named volume)
                                     │
                              ./backups (host bind mount)
```

All server-side rendering uses Django templates. No JavaScript framework or frontend build pipeline.

---

## 2. Django Project Structure

```
miniimpbox/                   ← repository root
├── config/                   ← Django project package
│   ├── __init__.py
│   ├── settings.py           ← single settings file (dev/trial)
│   ├── urls.py
│   └── wsgi.py
├── proposals/                ← proposals Django app
│   ├── __init__.py
│   ├── models.py             ← Proposal, StatusHistory
│   ├── forms.py              ← ProposalForm, StatusChangeForm
│   ├── views.py              ← all proposal views (public + admin)
│   ├── urls.py
│   ├── templates/
│   │   └── proposals/
│   │       ├── submit.html
│   │       ├── submit_complete.html
│   │       ├── admin_list.html
│   │       ├── admin_detail.html
│   │       └── admin_status_change.html
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_forms.py
│       └── test_views.py
├── accounts/                 ← accounts Django app
│   ├── __init__.py
│   ├── models.py             ← AdminLoginLog
│   ├── backends.py           ← EmailBackend (email-based auth)
│   ├── views.py              ← AdminLoginView, AdminLogoutView
│   ├── urls.py
│   ├── management/
│   │   └── commands/
│   │       └── seed_admin.py ← management command
│   ├── templates/
│   │   └── accounts/
│   │       └── login.html
│   └── tests/
│       ├── __init__.py
│       └── test_views.py
├── templates/                ← shared base templates
│   └── base.html
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── scripts/
    └── backup.sh
```

**[Assumption]** A single `config/settings.py` is used for both development and trial. There is no separate `settings/production.py` in v1. If production deployment is later approved, settings must be split before that point.

**Note on `django.contrib.admin`:** It is excluded from `INSTALLED_APPS` entirely. This means the Django admin site is unavailable at any URL. The `django_admin_log` table and the admin `Permission` model are not created.

---

## 3. Data Model

### 3.1 `proposals.Proposal`

```python
class Proposal(models.Model):
    STATUS_NEW       = 'new'
    STATUS_REVIEWING = 'reviewing'
    STATUS_PLANNED   = 'planned'
    STATUS_DONE      = 'done'
    STATUS_DECLINED  = 'declined'

    STATUS_CHOICES = [
        (STATUS_NEW,       'New'),
        (STATUS_REVIEWING, 'Reviewing'),
        (STATUS_PLANNED,   'Planned'),
        (STATUS_DONE,      'Done'),
        (STATUS_DECLINED,  'Declined'),
    ]
    VALID_STATUSES = {s[0] for s in STATUS_CHOICES}

    title             = models.CharField(max_length=100)
    body              = models.TextField()         # max length enforced at form layer (2000)
    submitter_name    = models.CharField(max_length=100, blank=True, default='')
    submitter_contact = models.CharField(max_length=254, blank=True, default='')
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                         default=STATUS_NEW, db_index=True)
    created_at        = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
```

**Notes:**
- `body` uses `TextField` (no `max_length` at DB level). The 2000-character limit is enforced in `ProposalForm.clean_body()`.
- `submitter_contact` stores the email string as plain text. Format validation is in `ProposalForm`. It is NOT a FK or EmailField at the model level, to avoid incidental validation on data already in the DB.
- `status` is indexed for potential future filtering; ordering uses `created_at`.
- `submitter_name` and `submitter_contact` must never appear in application logs (ADR-005, HD-19).

### 3.2 `proposals.StatusHistory`

```python
class StatusHistory(models.Model):
    proposal   = models.ForeignKey(
        Proposal, on_delete=models.PROTECT, related_name='status_history'
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='status_changes'
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['changed_at']
```

**Notes:**
- `on_delete=models.PROTECT` on both FKs: prevents accidental deletion of a proposal or admin user that has history records.
- `StatusHistory` rows are **append-only**. No `update()` or `delete()` calls are permitted on this model in application code (ADR-005).
- Written within the same `transaction.atomic()` block as the `Proposal.status` update (ADR-005).

### 3.3 `accounts.AdminLoginLog`

```python
class AdminLoginLog(models.Model):
    email        = models.CharField(max_length=254)   # stores attempted value; not FK
    success      = models.BooleanField()
    ip_address   = models.GenericIPAddressField(null=True, blank=True)  # see Section 10
    attempted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-attempted_at']
```

**Notes:**
- `email` is a plain `CharField`, not a FK to the User table. It records the value as submitted, even if the email does not correspond to any user account.
- `AdminLoginLog` rows are **append-only** (ADR-005).
- `ip_address` is nullable pending privacy review (A-09, R-07 in requirements). Implementation populates it by default; see Section 10 for the human-decision item.

### 3.4 Admin User Model

Django's built-in `auth.User` model is used without modification. The `is_staff=True` flag identifies administrator accounts. `is_superuser` is set to `False` for all seed-created admins.

**Note:** The `username` field of `auth.User` is used internally but is not exposed to users. The email-based authentication backend (`accounts.backends.EmailBackend`) authenticates by `email` field, not by `username`. The seed script sets `username = email` for compatibility.

---

## 4. URL Design

### 4.1 Root URL configuration (`config/urls.py`)

```python
urlpatterns = [
    path('',             include('proposals.urls',  namespace='proposals')),
    path('admin-portal/', include('accounts.urls',  namespace='accounts')),
    path('admin-portal/proposals/', include('proposals.admin_urls', namespace='proposals_admin')),
]
```

Django admin (`django.contrib.admin`) is **not** enabled in v1. It is excluded from `INSTALLED_APPS`.

`proposals.urls` handles public-facing paths only.
`accounts.urls` handles `/admin-portal/login/` and `/admin-portal/logout/`.
`proposals.admin_urls` handles all admin proposal paths under `/admin-portal/proposals/`.

### 4.2 `proposals/urls.py` (public)

| Name | Path | View | Method | Auth |
|---|---|---|---|---|
| `proposals:submit` | `/` | `ProposalSubmitView` | GET, POST | Public |
| `proposals:submit_complete` | `/submit/complete/` | `ProposalSubmitCompleteView` | GET | Public |

### 4.3 `proposals/admin_urls.py` (admin portal — included under `/admin-portal/proposals/`)

| Name | Path (full) | View | Method | Auth |
|---|---|---|---|---|
| `proposals_admin:list` | `/admin-portal/proposals/` | `AdminProposalListView` | GET | Admin |
| `proposals_admin:detail` | `/admin-portal/proposals/<int:pk>/` | `AdminProposalDetailView` | GET | Admin |
| `proposals_admin:status_change` | `/admin-portal/proposals/<int:pk>/status/` | `AdminStatusChangeView` | POST | Admin |

### 4.4 `accounts/urls.py`

| Name | Path | View | Method | Auth |
|---|---|---|---|---|
| `accounts:login` | `/admin-portal/login/` | `AdminLoginView` | GET, POST | Public |
| `accounts:logout` | `/admin-portal/logout/` | `AdminLogoutView` | POST | Admin |

---

## 5. View Design

### 5.1 Public Views (`proposals/views.py`)

**`ProposalSubmitView`**
- GET: Render `proposals/submit.html` with an empty `ProposalForm`.
- POST: Validate `ProposalForm`. On success, save `Proposal` (status=`new`) and redirect to `proposals:submit_complete`. On failure, re-render the form with errors.
- No authentication check.

**`ProposalSubmitCompleteView`**
- GET: Render `proposals/submit_complete.html` with a success message.
- No authentication check.

### 5.2 Admin Views (`proposals/views.py`)

All admin views use the `@admin_required` decorator (see Section 7.2). Unauthenticated requests are redirected to `accounts:login`.

**`AdminProposalListView`**
- GET: Query all `Proposal` objects ordered by `-created_at`. Paginate at 20 per page using Django's `Paginator`. Render `proposals/admin_list.html` with page object.
- No search, filter, or sort controls (HD-11, FR-ADMIN-03).

**`AdminProposalDetailView`**
- GET: Retrieve `Proposal` by `pk` (404 if not found). Fetch related `StatusHistory` ordered by `changed_at`. Render `proposals/admin_detail.html` with proposal, history, and a `StatusChangeForm`.

**`AdminStatusChangeView`**
- POST only (`@require_POST`). Retrieve `Proposal` by `pk`. Validate `StatusChangeForm`. On success: update status and write `StatusHistory` in `transaction.atomic()`. Redirect to `proposals_admin:detail`. On form validation failure: redirect back to detail with an error flag (or re-render; to be decided in implementation).
- Invalid status values are rejected by `StatusChangeForm` (ADR, HD-08).

### 5.3 Account Views (`accounts/views.py`)

**`AdminLoginView`**
- GET: Render `accounts/login.html` with an empty login form. If already authenticated and `is_staff`, redirect to `proposals_admin:list`.
- POST: Read `email` and `password` from POST body. Call `authenticate()`. Write `AdminLoginLog` (success or failure). On success: call `login()` and redirect to `proposals_admin:list`. On failure: re-render with generic error message `"Invalid email address or password."` (FR-AUTH-05).

**`AdminLogoutView`**
- POST only. Call `logout()` (invalidates server-side session). Redirect to `accounts:login`.

---

## 6. Authentication Implementation

*(Resolves ADR-001 deferred items)*

### 6.1 Email Authentication Backend

Django authenticates against `username` by default. Since admins log in with email, a custom backend is required.

**`accounts/backends.py`**

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailBackend(ModelBackend):
    """Authenticate using email field instead of username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Run password hash to mitigate timing attacks
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
```

**`config/settings.py`**

```python
AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']
```

### 6.2 Session Configuration

```python
# config/settings.py
SESSION_ENGINE              = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE          = 28800   # 8 hours absolute maximum
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # also expires when browser closes
SESSION_COOKIE_HTTPONLY     = True    # prevent JS access to session cookie
SESSION_COOKIE_SAMESITE     = 'Lax'  # CSRF mitigation for same-site requests
SESSION_COOKIE_SECURE       = False   # see Section 10 — human decision required
SESSION_COOKIE_NAME         = 'miniimpbox_sessionid'
```

**[BD-01 — Decided 2026-05-11]** `SESSION_COOKIE_SECURE = False` is accepted for the Docker Compose trial environment, which runs over HTTP. The trial is accessed exclusively via localhost (`http://localhost:8000` or `http://127.0.0.1:8000`). This acceptance is strictly limited to localhost-only access. If the application is ever accessed over LAN, VPN, internet, or any non-localhost network path, HTTPS must be configured and `SESSION_COOKIE_SECURE` must be changed to `True` before use.

### 6.3 Password Hashing

Django's default `PASSWORD_HASHERS` is used (PBKDF2-SHA256 as the primary hasher). No override is needed.

### 6.4 Failed Login Behavior

- Error message returned on any failure: `"Invalid email address or password."` This message does not reveal whether the email address exists (FR-AUTH-05).
- **No login lockout** is implemented in v1. This is a known risk for brute-force attacks. Acceptable for a limited internal trial with a small number of known operators. Must be re-evaluated before any public-facing deployment.
- All login attempts (success and failure) are logged to `AdminLoginLog` (FR-AUTH-06, ADR-005).

### 6.5 Logout Behavior

- `AdminLogoutView` accepts only `POST` requests (prevents CSRF-based logout).
- On logout: `django.contrib.auth.logout(request)` is called, which flushes the session from the DB and clears the session cookie.
- After logout, the user is redirected to `/admin-portal/login/`.

### 6.6 Admin Seed Procedure

**`accounts/management/commands/seed_admin.py`**

```python
import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Create the initial admin account from environment variables.'

    def handle(self, *args, **options):
        email    = os.environ['DJANGO_ADMIN_EMAIL']
        password = os.environ['DJANGO_ADMIN_PASSWORD']
        User = get_user_model()

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'Admin already exists: {email}'))
            return

        User.objects.create_user(
            username=email,   # username field set to email for compatibility
            email=email,
            password=password,
            is_staff=True,
            is_superuser=False,
            is_active=True,
        )
        self.stdout.write(self.style.SUCCESS(f'Admin created: {email}'))
```

Run after `migrate`:

```bash
docker compose exec app python manage.py seed_admin
```

Credentials are sourced from the `.env` file via Docker Compose. They are never committed to the repository (ADR-001, ADR-004).

---

## 7. Authorization Implementation

*(Resolves ADR-002 deferred item: admin identification attribute)*

### 7.1 Admin Identification: `is_staff = True`

Administrator accounts are identified by `user.is_staff == True` on Django's built-in `auth.User` model. `is_superuser` is `False`. (Decided: ADR-002)

Rationale: `is_staff` is Django's standard attribute for "can access staff-only areas." Using it avoids a custom field and custom migration. The seed command sets `is_staff=True`. No `auth.User` with `is_staff=False` has admin access.

### 7.2 `@admin_required` Decorator

A shared decorator is defined to protect all admin views. It must be applied consistently to every admin view function or class-based view.

**`proposals/decorators.py`** (or `accounts/decorators.py` — placed in `accounts` for ownership clarity)

```python
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    """Require authenticated user with is_staff=True."""
    @wraps(view_func)
    @login_required(login_url='/admin-portal/login/')
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapped_view
```

For class-based views, a `AdminRequiredMixin` using `AccessMixin` is used. Both the decorator and mixin delegate to the same `is_staff` check.

**Rule:** Every admin URL handler must use `@admin_required` or `AdminRequiredMixin`. This is verified in code review. Access control tests must confirm unauthenticated and non-staff requests are rejected (SECURITY_POLICY.md, ADR-002).

### 7.3 CSRF Protection

Django's `CsrfViewMiddleware` is enabled (default). All POST forms must include `{% csrf_token %}`. AJAX requests (none in v1) would also require the CSRF header.

---

## 8. Form and Validation Design

### 8.1 `ProposalForm`

```python
from django import forms
from django.core.validators import EmailValidator
from .models import Proposal

class ProposalForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea,
        max_length=2000,
        strip=True,
    )
    submitter_name = forms.CharField(
        max_length=100,
        required=False,
        strip=True,
    )
    submitter_contact = forms.CharField(
        max_length=254,
        required=False,
        strip=True,
    )

    class Meta:
        model = Proposal
        fields = ['title', 'body', 'submitter_name', 'submitter_contact']

    def clean_submitter_contact(self):
        value = self.cleaned_data.get('submitter_contact', '').strip()
        if value:
            EmailValidator()(value)   # raises ValidationError if invalid format
        return value
```

**Validation rules (FR-PROP-03):**
- `title`: required, 1–100 chars, stripped.
- `body`: required, 1–2000 chars, stripped.
- `submitter_name`: optional, 0–100 chars, stripped.
- `submitter_contact`: optional, 0–254 chars; if non-empty, must be valid email format. Invalid format → `ValidationError` (FR-PROP-03: rejection, not silent truncation).

### 8.2 `StatusChangeForm`

```python
from django import forms
from .models import Proposal

class StatusChangeForm(forms.Form):
    new_status = forms.ChoiceField(choices=Proposal.STATUS_CHOICES)
```

- The choices list is defined from `Proposal.STATUS_CHOICES`. Any value not in this set is rejected by Django's `ChoiceField` validation (FR-ADMIN-07, HD-08).

### 8.3 Login Form

A simple HTML form in `accounts/login.html` (not a Django `Form` subclass). Fields: `email` (text input), `password` (password input), `{% csrf_token %}`.

---

## 9. Audit Log Implementation

*(ADR-005)*

### 9.1 Status Change — within `AdminStatusChangeView`

```python
from django.db import transaction

with transaction.atomic():
    old_status = proposal.status
    proposal.status = new_status
    proposal.save(update_fields=['status', 'updated_at'])
    StatusHistory.objects.create(
        proposal=proposal,
        changed_by=request.user,
        old_status=old_status,
        new_status=new_status,
    )
```

- Atomicity: if the `StatusHistory` insert fails, the `Proposal` update is also rolled back, and vice versa.
- `changed_by` is `request.user` — the authenticated administrator at the time of the request.
- `proposal.body`, `submitter_name`, `submitter_contact` are **never** passed to `StatusHistory`. (ADR-005)

### 9.2 Login Log — within `AdminLoginView`

```python
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

# In the POST handler:
AdminLoginLog.objects.create(
    email=email,             # submitted value; not validated against User table
    success=success,
    ip_address=get_client_ip(request),  # nullable; see BD-01 and Section 10
)
```

- The log entry is written **before** the redirect or error response, regardless of success or failure.
- `password` is **never** passed to `AdminLoginLog`. (ADR-005, HD-19)
- `get_client_ip` reads `X-Forwarded-For` if present (for reverse proxy setups), otherwise `REMOTE_ADDR`.

### 9.3 Append-Only Enforcement

Application code must never call `.update()`, `.delete()`, or `.filter(...).delete()` on `StatusHistory` or `AdminLoginLog` querysets. This constraint is enforced via code review and test (a test that confirms no such calls exist, or a model-level guard).

---

## 10. Human Decisions Required

| ID | Topic | Decision needed | Blocking? |
|---|---|---|---|
| BD-01 | `SESSION_COOKIE_SECURE` setting | **Decided (2026-05-11):** `SESSION_COOKIE_SECURE = False` is accepted for the Docker Compose trial environment. The trial is accessed exclusively via `http://localhost:8000` or `http://127.0.0.1:8000`. This acceptance is limited to localhost-only trial verification. If the application is accessed over LAN, VPN, internet, or any non-localhost network path, HTTPS must be configured and `SESSION_COOKIE_SECURE` must be changed to `True` before use. | Resolved — no longer blocking |
| BD-02 | `ip_address` in `AdminLoginLog` | Currently populated by default (nullable on error). Confirm whether IP logging is permitted under applicable data handling rules (A-09, R-07 in requirements). If prohibited, set `ip_address=None` always. | Non-blocking for development; Release-blocking for trial start |

---

## 11. Error Handling

| Scenario | Behavior |
|---|---|
| Proposal form validation failure | Re-render `submit.html` with field errors. HTTP 200. |
| Status change form invalid | Redirect back to proposal detail with `?error=invalid_status` query param. Proposal is not changed. |
| Proposal not found (`pk` does not exist) | `get_object_or_404` → HTTP 404 with Django default 404 template. |
| Unauthenticated access to admin URL | Redirect to `/admin-portal/login/?next=<url>`. |
| Authenticated but non-staff access to admin URL | HTTP 403 (`PermissionDenied`). |
| POST to logout from unauthenticated session | Redirect to `/admin-portal/login/`. |
| Database error during status change | `transaction.atomic()` rolls back both `Proposal` and `StatusHistory`. Django raises `500` — standard Django error handling. No partial state is left. |
| Unexpected server error | Django's default error handling (HTTP 500). `DEBUG = False` in production/trial; no stack trace exposed to users. |

**Error message rule (SECURITY_POLICY.md):** Error messages shown to users must not expose internal details (model names, stack traces, SQL errors, existence of accounts). The login error message `"Invalid email address or password."` is the only auth-related user-facing error.

---

## 12. Django Settings

**`config/settings.py`** — key settings:

```python
import os

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'proposals',
    'accounts',
]
# django.contrib.admin is intentionally omitted in v1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # must be immediately after SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.environ['POSTGRES_DB'],
        'USER':     os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST':     os.environ.get('POSTGRES_HOST', 'db'),
        'PORT':     os.environ.get('POSTGRES_PORT', '5432'),
    }
}

AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']
LOGIN_URL           = '/admin-portal/login/'
LOGIN_REDIRECT_URL  = '/admin-portal/'
LOGOUT_REDIRECT_URL = '/admin-portal/login/'

SESSION_ENGINE               = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE           = 28800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY      = True
SESSION_COOKIE_SAMESITE      = 'Lax'
SESSION_COOKIE_SECURE        = False   # BD-01 decided: localhost-only trial; change to True if network access required
SESSION_COOKIE_NAME          = 'miniimpbox_sessionid'

STATIC_URL  = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LANGUAGE_CODE = 'ja'        # Japanese locale for admin-facing UI (or 'en-us')
TIME_ZONE     = 'Asia/Tokyo'
USE_TZ        = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging — ensure sensitive data is not logged
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}
```

**Log safety note:** Application code must never call `logger.info()`, `logger.debug()`, or `print()` with values from `proposal.body`, `proposal.submitter_name`, `proposal.submitter_contact`, passwords, or session tokens (HD-19, ADR-005).

---

## 13. Docker Compose Configuration

*(Resolves ADR-004 deferred items)*

**`docker-compose.yml`**

```yaml
services:
  app:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backups:/app/backups
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    env_file:
      - .env
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-miniimpbox}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

**`.env.example`** (committed to repository; contains no real secrets):

```
DJANGO_SECRET_KEY=change-this-to-a-long-random-string
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=miniimpbox
POSTGRES_USER=miniimpbox
POSTGRES_PASSWORD=change-this-password
POSTGRES_HOST=db
POSTGRES_PORT=5432
DJANGO_ADMIN_EMAIL=admin@example.com
DJANGO_ADMIN_PASSWORD=change-this-admin-password
BACKUP_GPG_PASSPHRASE=change-this-backup-passphrase
```

**`Dockerfile`** (outline):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --no-create-home appuser && chown -R appuser /app
USER appuser
```

---

## 14. Backup Configuration

*(Resolves ADR-004/ADR-006 deferred item: encryption tool)*

**Selected encryption tool: GPG symmetric encryption (AES-256)**

Rationale: GPG is available on most Linux systems without additional installation. Symmetric encryption with a passphrase avoids the complexity of key pair management. The passphrase is stored as `BACKUP_GPG_PASSPHRASE` in the `.env` file on the host (not in the container or repository). (ADR-004, ADR-006)

**`scripts/backup.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Load env vars (if not already in environment)
if [ -f "$(dirname "$0")/../.env" ]; then
  # shellcheck disable=SC1091
  set -a; source "$(dirname "$0")/../.env"; set +a
fi

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATE=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="backup_${DATE}.sql.gz"
ENC_FILE="${DUMP_FILE}.gpg"

mkdir -p "$BACKUP_DIR"

echo "Starting backup: $ENC_FILE"

# Dump and compress inside the db container, pipe through encryption on host
docker compose exec -T db \
  pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" \
  | gzip \
  | gpg --batch --yes --symmetric \
        --cipher-algo AES256 \
        --passphrase-fd 3 \
        --output "${BACKUP_DIR}/${ENC_FILE}" \
        /dev/stdin \
  3< <(printf '%s' "${BACKUP_GPG_PASSPHRASE}")

echo "Backup written: ${BACKUP_DIR}/${ENC_FILE}"

# Rotate: keep only the 14 most recent backup files
mapfile -t OLD_FILES < <(
  ls -t "${BACKUP_DIR}"/backup_*.sql.gz.gpg 2>/dev/null | tail -n +15
)
if [ "${#OLD_FILES[@]}" -gt 0 ]; then
  echo "Removing ${#OLD_FILES[@]} old backup(s)"
  rm -- "${OLD_FILES[@]}"
fi

echo "Backup complete."
```

**Schedule:** Run manually or via host cron (e.g., `0 2 * * * /path/to/backup.sh >> /var/log/miniimpbox-backup.log 2>&1`). The backup runs against the running Docker Compose stack.

**Backup key management:**
- `BACKUP_GPG_PASSPHRASE` lives only in the host `.env` file.
- It must **not** be stored in the `./backups/` directory or committed to the repository.
- The system owner must record the passphrase in a separate secure location (e.g., password manager) before the trial begins.

**Restore procedure (outline):**
```bash
# Decrypt
gpg --decrypt backup_YYYYMMDD_HHMMSS.sql.gz.gpg | gunzip > restore.sql
# Restore
docker compose exec -T db psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" < restore.sql
```

A full restore test must be performed at least once before relying on backups (ADR-004 Notes).

---

## 15. Package Versions (`requirements.txt`)

```
Django==5.2.1
psycopg[binary]==3.2.4
gunicorn==23.0.0
whitenoise==6.7.0
pytest==8.3.5
pytest-django==4.9.0
```

**[Assumption]** Minor patch versions above are approximate; exact versions must be pinned at implementation time using `pip freeze` or a lockfile tool. Dependencies must not be left as floating ranges (ADR-003 Notes).

---

## 16. Static Files

**Serving approach:** [WhiteNoise](https://whitenoise.readthedocs.io/) (`whitenoise`) is used to serve static files directly from gunicorn in the Docker Compose trial environment. WhiteNoise is added as WSGI middleware; no separate static file server or CDN is required for the trial.

This is the correct approach for the Docker Compose setup: Django's `DEBUG = False` means `django.contrib.staticfiles` does not serve files at runtime, and gunicorn itself is not a static file server. WhiteNoise bridges this gap with minimal configuration.

**`config/settings.py` additions:**

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # immediately after SecurityMiddleware
    ...
]

STATIC_URL  = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**`requirements.txt` addition:** `whitenoise==6.7.0`

**`docker-compose.yml`:** The existing `python manage.py collectstatic --noinput` step in the startup command populates `STATIC_ROOT` before gunicorn starts. WhiteNoise then serves files from `STATIC_ROOT` at the `/static/` prefix.

**[Assumption BD-A-04 / BD-A-06 revised]** v1 has minimal static file content (no JavaScript framework; minimal CSS in one or a few stylesheet files). `collectstatic` output is small. Serving via WhiteNoise is appropriate for a localhost trial with low concurrent users. This is not a production static file serving strategy; a CDN or dedicated file server would be required before any public-facing deployment.

---

## 17. Assumptions

| ID | Assumption |
|---|---|
| BD-A-01 | The trial is accessed via localhost (127.0.0.1 or ::1) only. `SESSION_COOKIE_SECURE = False` is acceptable under this assumption. (See BD-01.) |
| BD-A-02 | A single `config/settings.py` is sufficient for v1. Settings split for production is out of scope. |
| BD-A-03 | `django.contrib.admin` is not enabled in v1. The Django admin site is not used. |
| BD-A-04 | Minimal CSS, no JavaScript framework. UI complexity is in scope only as needed for form rendering and simple list/detail pages. |
| BD-A-05 | `gunicorn` with `--workers 2` is sufficient for limited internal trial concurrency. |
| BD-A-06 | Static files are served by WhiteNoise middleware for the Docker Compose trial. No separate static file server or CDN is required. Acceptable for localhost trial only. |
| BD-A-07 | The `LANGUAGE_CODE` and `TIME_ZONE` are set to Japanese locale. If English is preferred for admin UI, these can be changed before trial. |
| BD-A-08 | No email sending infrastructure is required (no notifications, no password reset). |
| BD-A-09 | GPG is available on the host machine running the backup script. If not, it must be installed before the trial begins. |

---

## 18. Risks

| ID | Risk | Severity | Note |
|---|---|---|---|
| R-BD-01 | `SESSION_COOKIE_SECURE = False` — session cookie transmitted over HTTP. If the trial host is accessed over a network, session tokens could be intercepted. | High | Accept only for localhost trial (BD-01). Add HTTPS if network access is needed. |
| R-BD-02 | No failed login lockout. Brute-force attack could enumerate valid admin emails if timing differences are observable. | Medium | Mitigated by constant-time dummy hash on missing accounts. Acceptable for internal trial. |
| R-BD-03 | `docker compose down --volumes` destroys `pgdata`. If run accidentally, all data is lost. | High | Document as forbidden in normal operations (ADR-004). Backup strategy mitigates data loss to at most one day. |
| R-BD-04 | Backup passphrase loss renders all encrypted backups unrecoverable. | High | Store passphrase in a password manager before trial. |
| R-BD-05 | `on_delete=models.PROTECT` on `StatusHistory.proposal` — deleting a proposal will raise a `ProtectedError`. Since proposal deletion is out of scope (HD-10), this is intentional, but an operator attempting DB-level deletion must handle this constraint. | Low | Documented in operational deletion procedure (ADR-006). |
| R-BD-06 | IP address logging (`ip_address` in `AdminLoginLog`) may conflict with applicable privacy rules. | Low | Nullable field; confirm under BD-02 before trial start. |

---

## 19. ADR Compliance Notes

| ADR | Compliance |
|---|---|
| ADR-001 | Email + password auth via `EmailBackend`. Server-side session, HTTP-only cookie. Session expiry 8h + browser close. PBKDF2-SHA256 default. Seed via management command. Login/logout views documented. ✓ |
| ADR-002 | `is_staff=True` as admin identifier. `@admin_required` decorator applied to all admin views. Authorization enforced server-side. ✓ |
| ADR-003 | Django 5.x + PostgreSQL 16 + Docker Compose. Django templates, no SPA. pytest + pytest-django. Package versions pinned in requirements.txt. ✓ |
| ADR-004 | `pgdata` named volume for DB. `./backups` host bind mount. `.env` for secrets. `docker compose down --volumes` flagged as destructive. ✓ |
| ADR-005 | `StatusHistory` and `AdminLoginLog` are append-only DB tables. Status change history written in same transaction as status update. Sensitive data (body, submitter_name, submitter_contact, password, session) never logged. ✓ |
| ADR-006 | GPG AES-256 symmetric encryption for backups. 14-generation rotation in backup script. Backup passphrase in `.env`, not in repository or backup dir. Operational deletion procedure referenced. ✓ |

---

## 20. Verification Strategy

The following areas require test coverage before the trial begins:

| Area | Required Tests | Risk Level |
|---|---|---|
| Proposal submission (valid) | Form saves, status=new, confirmation shown | Medium |
| Proposal submission (invalid) | Each invalid field case, email format validation for submitter_contact | Medium |
| Admin login (correct credentials) | Login log written (success=True), session created, redirect to list | High |
| Admin login (wrong credentials) | Login log written (success=False), no session, generic error message | High |
| Admin login (non-existent email) | Same behavior as wrong credentials (no account existence revealed) | High |
| Admin logout | Session invalidated, redirect to login | High |
| Unauthenticated access to admin URLs | Each admin URL → redirect to login | High |
| Non-staff access to admin URLs | HTTP 403 | High |
| Status change (valid) | Status updated, StatusHistory created, both in same transaction | High |
| Status change (invalid status value) | Rejected, proposal unchanged, no StatusHistory row | High |
| Proposal list pagination | Correct page size (20), navigation links | Low |
| Sensitive data in logs | No proposal body/submitter in log entries or DB log tables | High |
| `StatusHistory` append-only | No update/delete paths exist in application code | High |

Test-first validation is recommended for all High-risk items above (authentication, authorization, status change atomicity, sensitive data prohibition).

---

## 21. Document History

| Date | Author | Change |
|---|---|---|
| 2026-05-11 | AI Designer (Claude) | Initial draft created. All ADR-deferred items resolved: session design (Section 6), authorization attribute (Section 7.1), backup encryption tool (Section 14), Docker Compose config (Section 13), Django project structure (Section 2), URL/view design (Sections 4–5), form validation (Section 8). |
| 2026-05-11 | AI Designer (Claude) | Auto-fixable Design Review findings applied: URL routing restructured into proposals.urls / proposals.admin_urls / accounts.urls with correct `config/urls.py` includes (Section 4); django.contrib.admin exclusion clarified as INSTALLED_APPS omission (Section 2). |
| 2026-05-11 | System Owner (human) + AI Designer (Claude) | Human approved basic design. BD-01 decided: SESSION_COOKIE_SECURE=False accepted for localhost-only trial. Minor corrections applied: (1) admin URL namespace references aligned to proposals_admin:list / proposals_admin:detail throughout Sections 5.2 and 5.3; (2) static files design clarified — WhiteNoise added as the serving approach for Docker Compose trial (Sections 15, 16, 12 settings, BD-A-06). Document status changed to Approved. |

---

*This document has been approved by the System Owner (human) on 2026-05-11 and may be used as the basis for implementation planning. This approval covers the limited internal trial scope only. It does not constitute production release approval, public release approval, operational readiness approval, final implementation completion approval, or residual security/privacy risk acceptance.*
