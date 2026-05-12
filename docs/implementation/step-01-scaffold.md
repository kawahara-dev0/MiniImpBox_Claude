# Implementation Record — Step 1: Project Scaffold and Docker Compose

## Metadata

| Field | Value |
|---|---|
| Roadmap step | Phase 1, Step 1 — Project scaffold and Docker Compose environment |
| Implementation request | docs/implementation/implementation-request-v1.md |
| Roadmap | docs/design/roadmap-v1.md |
| Date | 2026-05-12 |
| Builder | AI Builder (Claude, Cowork mode) |
| Status | Pending Implementation Reviewer sign-off |

---

## 1. Scope

Step 1 creates the Django project scaffold and Docker Compose environment from scratch.
No business logic, authentication, or data models are included in this step.

**In scope (per roadmap-v1.md Step 1):**

- `requirements.txt` — pinned package versions
- `manage.py` — Django management utility
- `config/` — Django project package: `__init__.py`, `settings.py`, `urls.py`, `wsgi.py`
- `proposals/` — app package: `__init__.py`, placeholder `urls.py`, placeholder `admin_urls.py`, `tests/__init__.py`
- `accounts/` — app package: `__init__.py`, placeholder `urls.py`, `tests/__init__.py`
- `Dockerfile` — Python 3.12-slim, non-root user
- `docker-compose.yml` — app + db services, pgdata volume, backups bind mount
- `.env.example` — placeholder values, destructive command warning, passphrase storage note
- `.gitignore` — updated to add `backups/` entry
- `pytest.ini` — DJANGO_SETTINGS_MODULE = config.settings

**Out of scope (deferred to later steps):**

- Data models and migrations (Step 2)
- Authentication backend, views, forms (Steps 3–7)
- Templates (Steps 4, 6, 7)
- Backup script (Step 8)
- Test cases with automated assertions (Steps 2–9)

---

## 2. Changed Files

| File | Action | Rationale |
|---|---|---|
| `requirements.txt` | Created | Pinned package versions as specified in basic design Section 15 |
| `manage.py` | Created | Standard Django project management entry point |
| `config/__init__.py` | Created | Django project package marker |
| `config/settings.py` | Created | All settings per basic design Section 12; includes session, auth, DB, static, logging |
| `config/urls.py` | Created | Root URL conf with three namespace includes per basic design Section 4.1 |
| `config/wsgi.py` | Created | Standard WSGI entry point |
| `proposals/__init__.py` | Created | App package marker |
| `proposals/urls.py` | Created | Placeholder URL module (`app_name='proposals'`, `urlpatterns=[]`) |
| `proposals/admin_urls.py` | Created | Placeholder URL module (`app_name='proposals_admin'`, `urlpatterns=[]`) |
| `proposals/tests/__init__.py` | Created | Test package marker (populated in later steps) |
| `accounts/__init__.py` | Created | App package marker |
| `accounts/urls.py` | Created | Placeholder URL module (`app_name='accounts'`, `urlpatterns=[]`) |
| `accounts/tests/__init__.py` | Created | Test package marker (populated in later steps) |
| `Dockerfile` | Created | Python 3.12-slim, pip install, non-root appuser per basic design Section 13 |
| `docker-compose.yml` | Created | app + db services, pgdata named volume, backups bind mount per basic design Section 13 |
| `.env.example` | Created | Placeholder values, BACKUP_GPG_PASSPHRASE storage note, destructive command warning per ADR-004 / ADR-006 |
| `.gitignore` | Updated | Added `backups/` entry; all other needed entries were already present |
| `pytest.ini` | Created | Infrastructure for pytest-django; DJANGO_SETTINGS_MODULE set for Step 2+ test runs |
| `docs/tests/miniimpbox_v1_test_cases.csv` | Created | Step 1 acceptance criteria rows (S1-1 through S1-4) |

---

## 3. Implementation Notes and Assumptions

**SA-01 (Assumption): `STATICFILES_STORAGE` deprecation**
The approved basic design specifies `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`. This setting is deprecated in Django 4.2+ (replaced by `STORAGES`). It remains functional in Django 5.2.1 and will not block `manage.py check`. The deprecation warning is non-blocking for v1. Migration to `STORAGES` can be deferred to a future step or v2.

**SA-02 (Assumption): Package versions**
Exact versions in `requirements.txt` follow the roadmap specification exactly (Django 5.2.1, psycopg[binary] 3.2.4, gunicorn 23.0.0, whitenoise 6.7.0, pytest 8.3.5, pytest-django 4.9.0). The roadmap notes that "exact versions must be confirmed using `pip freeze` at implementation time." Since `pip freeze` cannot be run before Docker is available, these versions are confirmed at the approved design level. The human verifier should confirm these resolve correctly when `docker compose up` is first run.

**SA-03 (Assumption): `TEMPLATES` and other standard Django settings**
The basic design Section 12 shows only key settings. Standard required settings not in the snippet (`BASE_DIR`, `TEMPLATES`, `ROOT_URLCONF`, `WSGI_APPLICATION`, `USE_I18N`, `AUTH_PASSWORD_VALIDATORS`) were added following Django defaults. These do not change any approved decision.

**SA-04 (Assumption): `AUTH_PASSWORD_VALIDATORS = []`**
Django's built-in password validators are not used because `EmailBackend` handles authentication directly (ADR-001). An empty list is set to suppress Django system check warnings.

**SA-05 (Assumption): `pytest.ini`**
Added as infrastructure for pytest-django; not listed explicitly in the roadmap but required for `pytest` to discover the Django settings. No business behavior is affected.

---

## 4. Checks Run

| Check | Result | Notes |
|---|---|---|
| Static review of `config/settings.py` against basic design Section 12 | Pass | All required settings present; standard additions (TEMPLATES etc.) follow Django defaults |
| Static review of `config/urls.py` against basic design Section 4.1 | Pass | Three includes with correct namespaces |
| Static review of `docker-compose.yml` against basic design Section 13 | Pass | Matches exactly |
| Static review of `.env.example` against basic design Section 13 | Pass | All keys present; destructive command warning added per ADR-004 |
| Static review of `Dockerfile` against basic design Section 13 | Pass | Matches exactly |
| Static review of `requirements.txt` against basic design Section 15 | Pass | All six packages at specified versions |
| Static review of placeholder URL modules | Pass | `app_name` set correctly; `urlpatterns = []` |
| `.gitignore` check — `.env` excluded | Pass | Confirmed in file |
| `.gitignore` check — `backups/` added | Pass | Added in this step |
| Automated tests run | N/A | No automated tests for Step 1 (scaffold only; no business logic) |
| Lint (flake8/ruff) | Not run | Cannot run without Docker environment available. To be confirmed in Docker by human verifier. |
| CI | Not configured | CI not configured for this project. Status: not run. |

---

## 5. Test Case CSV Status

| File | Status |
|---|---|
| `docs/tests/miniimpbox_v1_test_cases.csv` | Created — rows S1-1 through S1-4 added for Step 1 acceptance criteria |

S1-1 (AI review — `.gitignore`): **Pass** (verified during this step).
S1-2 through S1-4: **Pending** — require Docker environment; part of Human Gate 1.

**Coverage CSV:** Not created in Step 1. No application modules with coverage targets exist yet. Created in Step 9.

---

## 6. Implementation Reviewer Outcome

**Reviewer:** AI Implementation Reviewer (Claude, Cowork mode) — independent of Builder
**Review date:** 2026-05-12

### Scope reviewed

- All 19 created/updated files listed in Section 2
- Implementation record Section 1–5
- test case CSV rows S1-1 through S1-4
- Compliance against: basic design Section 12, 13, 15; ADR-001 through ADR-006; roadmap Step 1 scope

### Findings

**Finding R1 — Non-blocking — `LOGIN_REDIRECT_URL` value**

`config/settings.py` sets `LOGIN_REDIRECT_URL = '/admin-portal/'`. The admin proposal list is at `/admin-portal/proposals/` (`proposals_admin:list`). If Django's built-in redirect uses this setting, it may result in a 404 because no URL pattern matches `/admin-portal/` exactly (the `accounts.urls` include handles paths *under* `admin-portal/` but there is no root `admin-portal/` route). The basic design Section 12 specifies this exact value, so it is retained. The Step 4 Builder must ensure `AdminLoginView` redirects explicitly to `proposals_admin:list` (not relying on `LOGIN_REDIRECT_URL`). This is already specified in basic design Section 5.3.

Classification: Non-blocking. No code change required for Step 1. Flag for Step 4 Builder.

**Finding R2 — Non-blocking — `STATICFILES_STORAGE` deprecation**

Django 4.2+ deprecates `STATICFILES_STORAGE` in favour of `STORAGES`. The basic design explicitly specifies the deprecated form. Functional in Django 5.2.1; non-blocking deprecation warning on `manage.py check`. Noted in SA-01. No action required for v1 scope.

Classification: Non-blocking.

**Finding R3 — Non-blocking — `pytest.ini` added outside explicit roadmap scope**

`pytest.ini` is required infrastructure for pytest-django and does not change any approved decision. Acceptable as SA-05. No action required.

Classification: Non-blocking.

### ADR compliance review

| ADR | Finding |
|---|---|
| ADR-001 | Session settings, LOGIN_URL, AUTHENTICATION_BACKENDS all correct ✓ |
| ADR-002 | LOGIN_URL, LOGOUT_REDIRECT_URL set; placeholder URL modules have correct namespaces ✓ |
| ADR-003 | All six packages pinned at exact versions per roadmap spec ✓ |
| ADR-004 | pgdata volume, backups bind mount, .env exclusion, destructive command warning all present ✓ |
| ADR-005 | N/A for Step 1 (no audit log code) |
| ADR-006 | BACKUP_GPG_PASSPHRASE documented with secure storage note ✓ |

### Security review

- `SECRET_KEY`, `POSTGRES_PASSWORD`, `POSTGRES_USER`, `POSTGRES_DB` all read from environment; none hardcoded ✓
- `SESSION_COOKIE_SECURE = False` per BD-01 (localhost-only trial accepted) ✓
- `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'` ✓
- `django.contrib.admin` excluded from INSTALLED_APPS ✓
- `.env` listed in `.gitignore` ✓
- No secrets in `.env.example` ✓

### Test adequacy review (no separate Tester)

Step 1 contains no application behavior (scaffold only). No automated tests are expected or required. The test case CSV correctly captures:
- S1-1 (AI review, N/A gate): `.gitignore` correctness — verified during this review ✓
- S1-2 through S1-4 (Human, Phase-blocking): Docker environment checks — correctly deferred to human verification (Gate 1)

Test adequacy is confirmed as appropriate for a Low-risk infrastructure step.

### Overall finding

**No blocking findings.** All three findings are non-blocking. Step 1 is ready to commit.

The Builder report is accurate and complete. Assumptions SA-01 through SA-05 are reasonable and documented. Human Gate 1 items are correctly classified and listed.

---

## 7. Tester

**Tester used:** No.

**Rationale:** Step 1 is classified as Low risk (no business logic, no authentication, no data models). The acceptance criteria are infrastructure checks (docker compose, manage.py check, volume persistence). Test adequacy is reviewed by the Implementation Reviewer.

**Reviewer test adequacy review:** See Section 6.

---

## 8. Human Verification Items

| ID | Item | Classification | Status |
|---|---|---|---|
| HV-S1-1 | `docker compose up` starts app and db without error | Phase-blocking (Gate 1) | Pending |
| HV-S1-2 | `manage.py check` passes with no system check errors | Phase-blocking (Gate 1) | Pending |
| HV-S1-3 | `docker compose down` / `docker compose up` preserves pgdata volume | Phase-blocking (Gate 1) | Pending |
| HV-S1-4 | `.env` is not committed; `.env.example` has only placeholder values | Phase-blocking (Gate 1) | Pending |

**Gate note:** HV-S1-1 through HV-S1-4 are part of Human Gate 1 (Environment Verification). Gate 1 must be cleared before Phase 2 begins. Human records gate decision in `docs/implementation/gate-01-environment.md`.

---

## 9. Assumptions and Remaining Risks

| ID | Type | Description |
|---|---|---|
| SA-01 | Assumption | STATICFILES_STORAGE deprecation — non-blocking for v1 |
| SA-02 | Assumption | Package versions match roadmap spec; pip freeze confirmation deferred to Docker environment |
| SA-03 | Assumption | Standard Django settings added beyond basic design snippet; no approved decision changed |
| SA-04 | Assumption | AUTH_PASSWORD_VALIDATORS = [] — acceptable for custom EmailBackend |
| SA-05 | Assumption | pytest.ini added as infrastructure; not listed in roadmap explicitly |
| BD-02 | Risk | ip_address logging decision (AdminLoginLog) — remains pending; non-blocking for development; release-blocking for trial start |

---

## 10. ADR Compliance Notes

| ADR | Compliance |
|---|---|
| ADR-001 | `AUTHENTICATION_BACKENDS`, session settings (all values) in settings.py ✓ |
| ADR-002 | `LOGIN_URL` set; placeholder URL modules allow correct namespace routing ✓ |
| ADR-003 | Django 5.2.1, psycopg[binary] 3.2.4, gunicorn 23.0.0, pytest 8.3.5, pytest-django 4.9.0 in requirements.txt ✓ |
| ADR-004 | `pgdata` named volume, `./backups` bind mount in docker-compose.yml; `.env` excluded from git; destructive command warning in .env.example ✓ |
| ADR-005 | N/A for Step 1 (no audit log code in this step) |
| ADR-006 | `BACKUP_GPG_PASSPHRASE` documented in `.env.example` with secure storage note ✓ |

---

## 11. Commit Hash

**Status:** Pending — git operations cannot be run from the AI Cowork shell because the workspace is mounted on a UNC path (`\\wsl.localhost\...`) that the Linux sandbox does not support. The commit must be created by the human operator using the command below.

**Required human action — commit command:**

```bash
cd <repo-root>   # MiniImpBox_Claude/
git add requirements.txt manage.py pytest.ini Dockerfile docker-compose.yml .env.example .gitignore \
       config/ proposals/ accounts/ \
       docs/tests/miniimpbox_v1_test_cases.csv \
       docs/implementation/step-01-scaffold.md
git commit -m "Step 1: Project scaffold and Docker Compose environment

- requirements.txt with pinned versions (Django 5.2.1, psycopg[binary] 3.2.4,
  gunicorn 23.0.0, whitenoise 6.7.0, pytest 8.3.5, pytest-django 4.9.0)
- config/settings.py, config/urls.py, config/wsgi.py
- proposals/ and accounts/ app packages with placeholder URL modules
- Dockerfile, docker-compose.yml, .env.example
- pytest.ini for pytest-django
- docs/tests/miniimpbox_v1_test_cases.csv (rows S1-1 to S1-4)
- docs/implementation/step-01-scaffold.md (Builder + Reviewer records)

Roadmap: Phase 1 Step 1
Implementation request: docs/implementation/implementation-request-v1.md"
```

After commit, update this section with the commit hash.

---

## 12. Push Status

**Status:** Pending — see Section 11.

**Gate check:** Step 1 has no phase-blocking gate that must be cleared before push. Human Gate 1 (Environment Verification) must be cleared before Phase 2 begins, but does not block the push of this commit. Push may proceed after the commit is created.

**Required human action — push command:**

```bash
git push
```

After push, if CI is configured, check the CI result. CI is not currently configured for this project.

---

*This implementation record is produced by the AI Builder. It is traceability evidence, not final acceptance, residual risk acceptance, or release approval.*
