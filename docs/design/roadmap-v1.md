# Development Roadmap — Mini Improvement Box v1

## Metadata

| Field | Value |
|---|---|
| Status | Approved |
| Version | v1 |
| Created | 2026-05-11 |
| Author | AI Designer (Claude, Cowork mode) |
| Approver | System Owner (human) — 2026-05-11 |
| Requirements basis | docs/requirements/requirements-v1.md (Approved 2026-05-11) |
| Basic design basis | docs/design/basic-design-v1.md (Approved 2026-05-11) |
| Implementation request | docs/implementation/implementation-request-v1.md |
| ADRs basis | ADR-001 through ADR-006 (All Accepted 2026-05-11) |
| Policies checked | AGENTS.md, DESIGN_WORKFLOW.md, REVIEW_POLICY.md, SECURITY_POLICY.md |

---

## Overview

This roadmap organizes the Mini Improvement Box v1 implementation into four phases, each ending with a human gate. It is derived from the approved basic design (`docs/design/basic-design-v1.md`) and the implementation request (`docs/implementation/implementation-request-v1.md`).

The roadmap does not change any decision made in the basic design or ADRs. It translates the approved design into an ordered sequence of implementation steps.

```
Phase 1: Environment and Foundation
  Step 1 — Project scaffold and Docker Compose
  Step 2 — Data models and migrations
  [ Human Gate 1: Environment verification ]

Phase 2: Authentication and Authorization  (High-risk)
  Step 3 — EmailBackend, session settings, seed_admin
  Step 4 — Account views and AdminLoginLog write
  Step 5 — @admin_required decorator and mixin
  [ Human Gate 2: End-to-end authentication verification ]

Phase 3: Application Features
  Step 6 — Public proposal submission
  Step 7 — Admin proposal views and status change
  [ Human Gate 3: Functional acceptance ]

Phase 4: Operations and Quality
  Step 8 — Backup script
  Step 9 — Test coverage, test case CSV, coverage CSV
  [ Human Gate 4: Trial readiness and manual verification ]
```

Each step produces a small, independently reviewable change. Each human gate must be cleared before the next phase begins.

**Per-step review requirement:** Every step must be reviewed by an Implementation Reviewer (independent of the Builder) before implementation of the next step begins. The Builder must not proceed to the next step without Reviewer sign-off. This applies to all steps, including low-risk ones. Human gate decision records replace the per-step Reviewer sign-off for the gate itself.

---

## Phase 1: Environment and Foundation

### Step 1 — Project scaffold and Docker Compose environment

**Scope:**

- Create `miniimpbox/` repository root with `config/`, `proposals/`, `accounts/` packages
- `manage.py`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `.gitignore`
- `requirements.txt` with pinned versions (Django 5.2.1, psycopg[binary] 3.2.4, gunicorn 23.0.0, whitenoise 6.7.0, pytest 8.3.5, pytest-django 4.9.0)
- `config/settings.py` — all settings from basic design Section 12: INSTALLED_APPS, MIDDLEWARE (with WhiteNoiseMiddleware), DATABASES, AUTHENTICATION_BACKENDS, session settings, LOGGING, STATIC_URL, STATIC_ROOT, STATICFILES_STORAGE
- `config/urls.py` — three includes: `proposals.urls`, `accounts.urls`, `proposals.admin_urls`
- `config/wsgi.py`
- Empty `proposals/__init__.py`, `accounts/__init__.py`
- **Placeholder URL modules** (empty `urlpatterns = []`, correct `app_name` set) so that `config/urls.py` can import them without error:
  - `proposals/urls.py` (`app_name = 'proposals'`)
  - `proposals/admin_urls.py` (`app_name = 'proposals_admin'`)
  - `accounts/urls.py` (`app_name = 'accounts'`)
  These placeholders are replaced with real URL patterns in Steps 4, 6, and 7.

**Acceptance criteria:**

- `docker compose up` starts both `app` and `db` services without error
- `docker compose exec app python manage.py check` passes (no system check errors) — this requires the placeholder URL modules to exist
- `docker compose down` followed by `docker compose up` preserves the `pgdata` volume
- `.env` is listed in `.gitignore`; no secret values are committed

**Implementation record:** `docs/implementation/step-01-scaffold.md`

**Risk:** Low — no business logic, no authentication

---

### Step 2 — Data models and migrations

**Scope:**

- `proposals/models.py`: `Proposal` (STATUS_CHOICES, VALID_STATUSES, all fields, Meta ordering), `StatusHistory` (PROTECT FKs, append-only, Meta ordering)
- `accounts/models.py`: `AdminLoginLog` (nullable ip_address, append-only, Meta ordering)
- Run `makemigrations` for both apps
- Run `migrate` to confirm all tables are created

**Acceptance criteria:**

- `python manage.py migrate` succeeds
- All model fields, types, and constraints match basic design Section 3 exactly
- `on_delete=models.PROTECT` on `StatusHistory.proposal` and `StatusHistory.changed_by`
- `ip_address` is `GenericIPAddressField(null=True, blank=True)` (BD-02 pending)

**Test coverage required:**

- Model unit tests: field defaults, `VALID_STATUSES` completeness, `STATUS_CHOICES` consistency
- Confirm `on_delete=PROTECT` raises `ProtectedError` when attempting to delete a referenced proposal (regression guard)

**Implementation record:** `docs/implementation/step-02-models.md`

**Risk:** Low — no authentication logic; schema-only change

---

### Human Gate 1: Environment verification

**Blocking:** Phase 2 must not begin until this gate is cleared.

**Human verification required:**

1. `docker compose up` starts successfully from a clean environment (no cached data)
2. `python manage.py check` passes
3. `python manage.py migrate` succeeds; all expected tables are visible in PostgreSQL
4. `docker compose down` (without `--volumes`) followed by `docker compose up` — verify `pgdata` volume persists (no data loss)
5. Confirm `.env` is not committed; `.env.example` is committed with placeholder values

**AI does not clear this gate.** Human records gate decision in `docs/implementation/gate-01-environment.md`.

---

## Phase 2: Authentication and Authorization

**Risk level: High** — all steps in this phase touch authentication, authorization, and audit logging. Test-first validation is required for all steps in this phase.

---

### Step 3 — EmailBackend, session settings, seed_admin management command

**Scope:**

- `accounts/backends.py`: `EmailBackend` — query by `email`, constant-time dummy hash for non-existent accounts, `check_password()` + `user_can_authenticate()`
- Verify `AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']` is correctly set (already in Step 1 settings)
- `accounts/management/commands/seed_admin.py`: read `DJANGO_ADMIN_EMAIL` and `DJANGO_ADMIN_PASSWORD` from environment, create `is_staff=True`, `is_superuser=False` user; idempotent (no duplicate on second run)

**Acceptance criteria:**

- `EmailBackend.authenticate()` returns `None` for wrong email (after running dummy hash)
- `EmailBackend.authenticate()` returns `None` for wrong password
- `EmailBackend.authenticate()` returns the user for correct credentials
- Timing difference between "wrong email" and "wrong password" paths is not measurable (constant-time mitigation)
- `seed_admin` creates a user with `is_staff=True`, `is_superuser=False`, `username=email`
- Running `seed_admin` a second time with the same email does not create a duplicate

**Test-first required (all items).**

**Implementation record:** `docs/implementation/step-03-auth-backend.md`

**Risk:** High — authentication logic

---

### Step 4 — Account views: AdminLoginView, AdminLogoutView, AdminLoginLog write

**Scope:**

- `accounts/views.py`:
  - `AdminLoginView` (GET + POST): authenticate via `EmailBackend`, write `AdminLoginLog` on every attempt before response, `login()` on success, redirect to `proposals_admin:list` (`/admin-portal/proposals/`); generic error on failure
  - `AdminLogoutView` (POST only): `logout()`, redirect to `accounts:login`
- `accounts/urls.py`: `accounts:login` and `accounts:logout`
- `accounts/templates/accounts/login.html`: login form with `{% csrf_token %}`
- `templates/base.html`: shared base template (minimal structure)

**Acceptance criteria:**

- GET `/admin-portal/login/` renders login form
- POST with correct credentials: `AdminLoginLog` row written (success=True), session created, redirect to `/admin-portal/proposals/` (`proposals_admin:list`)
- POST with incorrect credentials: `AdminLoginLog` row written (success=False), no session, error message `"Invalid email address or password."` (no account existence hint)
- POST to `/admin-portal/logout/` from authenticated session: session invalidated, redirect to `/admin-portal/login/`
- GET to `/admin-portal/logout/` returns HTTP 405 (POST only)
- All login attempts write to `AdminLoginLog` regardless of success or failure
- `password` never appears in any `AdminLoginLog` column

**Test-first required (all items).**

**Implementation record:** `docs/implementation/step-04-account-views.md`

**Risk:** High — authentication, audit logging

---

### Step 5 — @admin_required decorator and AdminRequiredMixin

**Scope:**

- `accounts/decorators.py`: `admin_required` decorator — wraps `@login_required(login_url='/admin-portal/login/')` + `is_staff` check → `PermissionDenied` if not staff
- `AdminRequiredMixin` for class-based views — same logic
- Stub admin view to verify decorator behavior (will be replaced in Phase 3)

**Acceptance criteria:**

- Unauthenticated request to a decorator-protected view: redirect to `/admin-portal/login/?next=<url>`
- Authenticated non-staff request: HTTP 403
- Authenticated `is_staff=True` request: proceeds to view
- The same checks apply when using `AdminRequiredMixin`

**Test-first required (all items).**

**Implementation record:** `docs/implementation/step-05-authorization.md`

**Risk:** High — authorization enforcement

---

### Human Gate 2: End-to-end authentication verification

**Blocking:** Phase 3 must not begin until this gate is cleared.

**Human verification required:**

1. Run `seed_admin`, then open `http://localhost:8000/admin-portal/login/`
2. Login with incorrect credentials — verify generic error message, no session created; verify `AdminLoginLog` row (success=False) in database
3. Login with correct credentials — verify redirect to `/admin-portal/proposals/` (proposal list); verify `AdminLoginLog` row (success=True)
4. Logout — verify session invalidated; verify subsequent access to `/admin-portal/proposals/` redirects to login
5. Access `/admin-portal/proposals/` directly without a session — verify redirect to login with `?next=` parameter
6. Verify Django admin at `/admin/` is not reachable (expect 404 or connection refused, not the Django admin login page)
7. Verify that `password` does not appear anywhere in the `admin_login_log` table

**AI does not clear this gate.** Human records gate decision in `docs/implementation/gate-02-authentication.md`.

---

## Phase 3: Application Features

### Step 6 — Public proposal submission

**Scope:**

- `proposals/forms.py`: `ProposalForm` — title (required, 1-100), body (required, 1-2000, strip=True), submitter_name (optional, 0-100), submitter_contact (optional, 0-254, email format validation if non-empty)
- `proposals/views.py`: `ProposalSubmitView` (GET + POST), `ProposalSubmitCompleteView` (GET)
- `proposals/urls.py`: `proposals:submit`, `proposals:submit_complete`
- `proposals/templates/proposals/submit.html`, `proposals/templates/proposals/submit_complete.html`
- Confirm `Proposal` is created with `status='new'`

**Acceptance criteria:**

- GET `/` renders proposal form
- Valid POST (all fields): proposal saved with status=`new`, redirect to `/submit/complete/`
- Valid POST (title + body only, optional fields empty): proposal saved
- Invalid `submitter_contact` (non-empty, invalid email format): form error, no submission
- `body` > 2000 characters: form error, no submission
- `title` > 100 characters: form error, no submission
- Empty `title` or `body`: form error, no submission

**Implementation record:** `docs/implementation/step-06-public-submission.md`

**Risk:** Medium — public-facing form

---

### Step 7 — Admin proposal views and status change

**Scope:**

- `proposals/forms.py`: `StatusChangeForm` — `new_status` ChoiceField based on `Proposal.STATUS_CHOICES`
- `proposals/views.py`:
  - `AdminProposalListView` (GET, `@admin_required`, paginated 20/page)
  - `AdminProposalDetailView` (GET, `@admin_required`)
  - `AdminStatusChangeView` (POST, `@admin_required`, `@require_POST`, atomic status change + `StatusHistory` write)
- `proposals/admin_urls.py`: `proposals_admin:list`, `proposals_admin:detail`, `proposals_admin:status_change`
- `proposals/templates/proposals/admin_list.html`, `admin_detail.html`, `admin_status_change.html`

**Acceptance criteria:**

- GET `/admin-portal/proposals/`: lists proposals ordered by `-created_at`, 20 per page
- GET `/admin-portal/proposals/<pk>/`: shows proposal detail with status history
- POST `/admin-portal/proposals/<pk>/status/` with valid new_status: updates proposal status, creates `StatusHistory` row, both in same transaction, redirects to `proposals_admin:detail`
- POST with invalid status value: proposal unchanged, no `StatusHistory` row, no unhandled exception
- `proposal.body`, `submitter_name`, `submitter_contact` never appear in `StatusHistory` columns
- Unauthenticated access to any admin proposal URL: redirect to login
- Non-staff access: HTTP 403

**Test-first required for status change atomicity and sensitive data non-disclosure.**

**Implementation record:** `docs/implementation/step-07-admin-views.md`

**Risk:** High — status change atomicity, audit log integrity

---

### Human Gate 3: Functional acceptance

**Blocking:** Phase 4 must not begin until this gate is cleared.

**Human verification required:**

1. Submit a proposal via `/` — verify it appears in admin list
2. View proposal detail — verify all fields display correctly
3. Change proposal status — verify new status shown, `StatusHistory` row visible in detail
4. Change status again — verify history shows both changes in order
5. Verify paginator appears when more than 20 proposals exist (create test data if needed)
6. Verify proposal body and submitter fields do not appear in any `status_history` column (direct DB check)

**AI does not clear this gate.** Human records gate decision in `docs/implementation/gate-03-functional.md`.

---

## Phase 4: Operations and Quality

### Step 8 — Backup script

**Scope:**

- `scripts/backup.sh`: GPG AES-256 symmetric encryption, 14-generation rotation, `set -euo pipefail`
- Script is executable (`chmod +x`)
- Rotation logic handles zero existing files (no error on first run)
- Document `BACKUP_GPG_PASSPHRASE` usage in `.env.example` comment
- Document `docker compose down --volumes` as destructive in `.env.example` comment

**Acceptance criteria:**

- `scripts/backup.sh` runs against the Docker Compose stack and produces an encrypted file in `./backups/`
- File is named `backup_YYYYMMDD_HHMMSS.sql.gz.gpg`
- Running the script 15 times results in exactly 14 backup files (oldest removed)
- Running the script once when no backup files exist: succeeds, no rotation error
- `gpg --decrypt backup_*.gpg | gunzip > restore.sql` and restoring to DB succeeds (manual restore test — see Human Gate 4)

**Implementation record:** `docs/implementation/step-08-backup.md`

**Risk:** Medium — backup correctness; key management is operational risk, not code risk

---

### Step 9 — Test coverage, test case CSV, coverage CSV

**Scope:**

- Ensure all High-risk test areas from basic design Section 20 have test coverage
- `docs/tests/miniimpbox_v1_test_cases.csv`: complete test case records for all areas
- `docs/tests/coverage_result.csv`: coverage for High-risk modules (accounts/backends.py, accounts/views.py, proposals/views.py admin views, proposals/models.py, proposals/forms.py)
- Run full test suite; all tests must pass
- Run lint (flake8 or ruff); must pass

**Acceptance criteria:**

- All automated tests pass
- Lint passes
- Test case CSV covers all test areas in basic design Section 20
- Coverage CSV shows High-risk modules at target levels
- No `.update()` or `.delete()` calls on `StatusHistory` or `AdminLoginLog` in application code (confirmed by grep or test)

**Implementation record:** `docs/implementation/step-09-test-coverage.md`

---

### Human Gate 4: Trial readiness and manual verification

**Blocking:** Trial must not begin until all items in this gate are cleared.

**Release-blocking (before trial start):**

1. **Full manual verification** — perform all steps in implementation request Section 12:
   - Public submission (valid, each invalid case)
   - Admin login (correct, wrong credentials, non-existent email)
   - Admin logout
   - Admin URL access control (unauthenticated, non-staff)
   - Status change (valid and invalid)
   - Security spot checks (session isolation, CSRF, `/admin/` inaccessible)

2. **BD-02: IP address logging decision** — confirm whether `ip_address` in `AdminLoginLog` is permitted under applicable data handling rules. If prohibited, set `ip_address=None` always and update tests. Record decision in `docs/implementation/gate-04-trial-readiness.md`.

3. **Backup restore test** — decrypt a backup file, restore to DB, confirm data is intact. Record result in `docs/implementation/gate-04-trial-readiness.md` (ADR-004).

4. **Trial end date** — define and record the trial end date. Calculate and record the retention expiry date (trial end + 90 days). Set calendar reminder for the deletion date (ADR-006).

5. **Operational deletion procedure** — document the 7-step deletion procedure from ADR-006 before trial begins.

6. **GPG passphrase** — confirm `BACKUP_GPG_PASSPHRASE` is stored in a separate secure location (e.g., password manager) before trial begins. It must not be stored only in `.env` on the trial host.

**AI does not clear this gate.** Human records all decisions in `docs/implementation/gate-04-trial-readiness.md`.

---

## Human Gates Summary

| Gate | Phase boundary | Blocking type | Key items |
|---|---|---|---|
| Gate 1 | Before Phase 2 | Phase-blocking | Docker Compose environment, DB schema, volume persistence |
| Gate 2 | Before Phase 3 | Phase-blocking | End-to-end authentication, AdminLoginLog correctness, `/admin/` inaccessible |
| Gate 3 | Before Phase 4 | Phase-blocking | Proposal submission, admin portal functional acceptance, DB-level sensitive data check |
| Gate 4 | Before trial | Release-blocking | Full manual verification, BD-02 decision, backup restore test, trial end date, deletion procedure |

---

## Non-Blocking Items

The following items may be resolved during development without blocking any gate:

- BD-02: IP address logging — confirm under applicable data handling rules (must be resolved before Gate 4)
- `LANGUAGE_CODE` and `TIME_ZONE` — adjust before trial if English locale is preferred
- Package version pinning — exact patch versions must be confirmed using `pip freeze` at implementation time

---

## Risks

| ID | Risk | Severity | Mitigation |
|---|---|---|---|
| R-RM-01 | A gate is skipped due to time pressure, allowing unverified changes into the trial. | High | All gates are explicitly phase-blocking or release-blocking. AI cannot clear gates. |
| R-RM-02 | Authentication or authorization tests are written after implementation, reducing their value as correctness evidence. | High | Test-first is required for Phase 2 (Steps 3, 4, 5). |
| R-RM-03 | BD-02 (IP address logging) is not confirmed before trial start, creating potential data handling risk. | Medium | BD-02 is a release-blocking item in Gate 4. |
| R-RM-04 | Backup passphrase is stored only in `.env` on the trial host. If the host is compromised, backups can be decrypted. | High | Gate 4 requires confirming passphrase is stored in a separate secure location. |
| R-RM-05 | Operational deletion procedure is not documented before trial, leaving personal data at risk after retention period. | High | Gate 4 requires documenting the deletion procedure before trial. |
| R-RM-06 | Trial end date is not recorded, making it impossible to enforce the 90-day retention period. | Medium | Gate 4 requires recording trial end date and retention expiry before trial starts. |

---

## Assumptions

| ID | Assumption |
|---|---|
| RM-A-01 | The Builder will implement one step at a time and produce an implementation record for each step. |
| RM-A-02 | The Implementation Reviewer reviews each step before the next step begins. |
| RM-A-03 | Human gate decisions are recorded in `docs/implementation/gate-0N-*.md` files before the next phase begins. |
| RM-A-04 | GPG is available on the host machine before Step 8 is tested. |
| RM-A-05 | No production deployment is planned. This roadmap covers the localhost-only internal trial only (BD-01, HD-15-AI). |

---

## Implementation Records Index

Each step must produce an implementation record. All records are stored under `docs/implementation/`:

| Artifact | Description |
|---|---|
| `step-01-scaffold.md` | Builder report for Step 1 |
| `step-02-models.md` | Builder report for Step 2 |
| `gate-01-environment.md` | Human gate decision record for Gate 1 |
| `step-03-auth-backend.md` | Builder report for Step 3 |
| `step-04-account-views.md` | Builder report for Step 4 |
| `step-05-authorization.md` | Builder report for Step 5 |
| `gate-02-authentication.md` | Human gate decision record for Gate 2 |
| `step-06-public-submission.md` | Builder report for Step 6 |
| `step-07-admin-views.md` | Builder report for Step 7 |
| `gate-03-functional.md` | Human gate decision record for Gate 3 |
| `step-08-backup.md` | Builder report for Step 8 |
| `step-09-test-coverage.md` | Builder report for Step 9 |
| `gate-04-trial-readiness.md` | Human gate decision record for Gate 4 (trial start approval) |

---

## Document History

| Date | Author | Change |
|---|---|---|
| 2026-05-11 | AI Designer (Claude, Cowork mode) | Initial draft created. Four phases, nine steps, four human gates derived from approved basic design and implementation request. |
| 2026-05-11 | AI Designer (Claude, Cowork mode) | Auto-fixable Design Review findings applied: Gate 4 body labels corrected from "Phase-blocking" to "Release-blocking" for consistency with summary table; per-step Implementation Reviewer requirement added explicitly to Overview section. |
| 2026-05-11 | System Owner (human) + AI Designer (Claude, Cowork mode) | Human approved roadmap. Minor corrections applied: (1) admin portal list URL aligned — `/admin-portal/` references in Step 4 and Gate 2 replaced with `/admin-portal/proposals/` (`proposals_admin:list`); (2) Step 1 scope clarified — placeholder URL modules (`proposals/urls.py`, `proposals/admin_urls.py`, `accounts/urls.py`) added as required for `python manage.py check` to pass before feature views are implemented. Approval scope: implementation roadmap for v1 limited internal trial only; does not clear any implementation gate. |

---

*This document has been approved by the System Owner (human) on 2026-05-11 as the implementation roadmap for Mini Improvement Box v1 limited internal trial. This approval does not clear any implementation gate. Each step still requires Implementation Reviewer sign-off, and human gate decisions must be recorded as defined in the roadmap.*
