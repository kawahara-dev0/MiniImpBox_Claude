# Implementation Request — Mini Improvement Box v1

## 1. Request Summary

### Title

Initial full implementation of Mini Improvement Box v1 — Django proposal submission and admin portal

### Request Type

- [x] New feature

### Priority

- [x] High

### Risk Level

- [x] High risk

Risk justification: Authentication, authorization, audit logging, data integrity (atomic status change + history), and sensitive data non-disclosure are all in scope. These are all High-risk areas per the template.

---

## 2. Purpose

### Purpose

Build the Mini Improvement Box v1 application from scratch as defined in the approved basic design. The application allows general users (unauthenticated) to submit improvement proposals and allows administrators (email + password authenticated) to view and manage those proposals.

### Problem to Solve

No application currently exists. The basic design (`docs/design/basic-design-v1.md`) is approved and all architecture decisions have been made. Implementation can now begin.

### Expected Value

A working Django application running in Docker Compose that satisfies all requirements in `docs/requirements/requirements-v1.md` and all architectural decisions in ADR-001 through ADR-006.

---

## 3. Background

### Current Behavior

No code exists. This is a greenfield implementation.

### Desired Behavior

A Django 5.x web application with:
- Public proposal submission form at `/`
- Admin portal at `/admin-portal/` for authenticated administrators
- Session-based email + password authentication
- Proposal status management with atomic status change + audit history
- Administrator login logging
- Docker Compose environment with PostgreSQL 16, named volume for data, host bind mount for backups
- GPG-encrypted daily backup script

### Related Business Rules

All business rules are defined in `docs/requirements/requirements-v1.md` (Approved 2026-05-11).

### Related Design Notes

All design decisions are defined in `docs/design/basic-design-v1.md` (Approved 2026-05-11).

ADR basis: ADR-001 through ADR-006 (all Accepted 2026-05-11).

---

## 4. Scope

### In Scope

The following components must be implemented, exactly as specified in `docs/design/basic-design-v1.md`:

- Django project scaffold (`miniimpbox/` repository root as defined in Section 2)
- Data models: `Proposal`, `StatusHistory` (proposals app), `AdminLoginLog` (accounts app), plus migrations (Section 3)
- `EmailBackend` custom authentication backend (Section 6.1)
- Session settings as specified (Section 6.2)
- `seed_admin` management command (Section 6.6)
- `@admin_required` decorator and `AdminRequiredMixin` (Section 7.2)
- `ProposalForm` and `StatusChangeForm` (Section 8)
- Public views: `ProposalSubmitView`, `ProposalSubmitCompleteView` (Section 5.1)
- Admin views: `AdminProposalListView`, `AdminProposalDetailView`, `AdminStatusChangeView` (Section 5.2)
- Account views: `AdminLoginView`, `AdminLogoutView` (Section 5.3)
- URL configuration: `config/urls.py`, `proposals/urls.py`, `proposals/admin_urls.py`, `accounts/urls.py` (Section 4)
- Audit log implementation: atomic status change + `StatusHistory` write, `AdminLoginLog` write on every login attempt (Section 9)
- Django settings (`config/settings.py`) with all required settings (Section 12)
- Docker Compose configuration: `docker-compose.yml`, `Dockerfile`, `.env.example`, `.gitignore` (Section 13)
- Backup script: `scripts/backup.sh` with GPG AES-256 encryption and 14-generation rotation (Section 14)
- `requirements.txt` with pinned versions including `whitenoise==6.7.0` (Section 15)
- Static files: WhiteNoise configuration (Section 16)
- Django templates: `base.html`, `proposals/submit.html`, `proposals/submit_complete.html`, `proposals/admin_list.html`, `proposals/admin_detail.html`, `proposals/admin_status_change.html`, `accounts/login.html`
- Test files as specified in the project structure (Section 2)

### Target Files / Areas

All files under the `miniimpbox/` project root, as defined in the project structure (Section 2 of basic design). The full expected structure:

```
miniimpbox/
├── config/                   (settings.py, urls.py, wsgi.py, __init__.py)
├── proposals/                (models, forms, views, urls.py, admin_urls.py, templates/, tests/)
├── accounts/                 (models, backends.py, views, urls.py, management/commands/, templates/, tests/)
├── templates/base.html
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── scripts/backup.sh
```

### Allowed Change Types

- [x] UI change (templates)
- [x] API change (URLs and views)
- [x] Database schema change (models and migrations)
- [x] Business logic change (forms, views, status change logic)
- [x] Validation change (ProposalForm, StatusChangeForm)
- [x] Authorization change (decorator, mixin)
- [x] Test code change (new tests)
- [x] Configuration change (settings.py, docker-compose.yml, Dockerfile)

---

## 5. Out of Scope

The following items are explicitly out of scope for v1 and must not be implemented:

- Proposal deletion by any user or administrator (HD-10, FR-ADMIN-09, FR-PROP-06)
- Proposal search, filter, or sort controls (HD-11, FR-ADMIN-03)
- Proposal comments (HD-09)
- Failed login lockout / rate limiting (HD-12)
- Password reset or account management UI
- Email notifications (HD-08 out of scope)
- Administrator proposal view history logging (HD-19)
- Data export or erasure API (ADR-006)
- Django admin site (`django.contrib.admin`) — must remain excluded from `INSTALLED_APPS`
- Automated data lifecycle enforcement (ADR-006)
- Multi-settings environments (production settings split) — single `config/settings.py` only
- CDN or external static file server
- HTTPS / TLS configuration — trial is localhost-only (BD-01)
- Any feature not explicitly in `docs/requirements/requirements-v1.md` or `docs/design/basic-design-v1.md`

AI must not implement out-of-scope items even if they appear related or useful. If an out-of-scope issue is found, report it separately.

---

## 6. Requirements

### Functional Requirements

Refer to `docs/requirements/requirements-v1.md` for the authoritative list. The following are the critical requirements to verify during implementation:

- FR-PROP-01 to FR-PROP-06: Proposal submission form, validation, confirmation, no deletion
- FR-ADMIN-01 to FR-ADMIN-09: Admin login, proposal list (paginated 20/page), proposal detail, status change, status history display, no deletion
- FR-AUTH-01 to FR-AUTH-06: Email + password auth, generic error messages, session management, login logging

### Non-Functional Requirements

- NFR-01: All authentication and authorization checks server-side
- NFR-02: Sensitive data (proposal body, submitter_name, submitter_contact, passwords, session tokens) must never appear in any log or audit table
- NFR-03: Session cookie HTTP-only, SameSite=Lax, 8h max age + browser-close expiry
- NFR-04: All POST forms must include `{% csrf_token %}`
- NFR-05: `docker compose up` must start the full application; `docker compose down` (without `--volumes`) must preserve all data
- NFR-06: Application runs in Docker Compose (Docker Compose environment only for v1)
- NFR-07: Database data in named `pgdata` volume; backup files in host bind mount

### Error Handling Requirements

- Proposal form validation failure: re-render `submit.html` with field errors, HTTP 200
- Status change with invalid status: reject (form invalid), proposal unchanged, no `StatusHistory` row created
- `pk` not found: HTTP 404 via `get_object_or_404`
- Unauthenticated admin access: redirect to `/admin-portal/login/?next=<url>`
- Non-staff authenticated access: HTTP 403 (`PermissionDenied`)
- Database error during status change: `transaction.atomic()` rolls back both changes; HTTP 500

### Permission / Authorization Requirements

- Unauthenticated users: may access `/` and `/submit/complete/` only
- Authenticated non-staff users: may not access any `/admin-portal/` route (HTTP 403)
- Authenticated `is_staff=True` users: may access all `/admin-portal/` routes
- No user may delete proposals (application enforces this by providing no deletion endpoint)

### Data Consistency Requirements

- Status change and `StatusHistory` insert must be within a single `transaction.atomic()` block
- If either fails, both must be rolled back — no partial state
- `StatusHistory` and `AdminLoginLog` must be append-only: no `.update()` or `.delete()` calls on these models anywhere in application code
- `on_delete=models.PROTECT` on `StatusHistory.proposal` and `StatusHistory.changed_by` — these FKs must never cascade delete

### Audit / Logging Requirements

- Every login attempt (success and failure) must write one `AdminLoginLog` row before the response is sent
- Every status change must write one `StatusHistory` row within the same transaction as the status update
- The following data must **never** appear in `StatusHistory`, `AdminLoginLog`, Django application logs, or any other log: `proposal.body`, `proposal.submitter_name`, `proposal.submitter_contact`, passwords (in any form), session tokens or session IDs

---

## 7. Constraints

### Architectural Constraints

- All accepted ADRs (ADR-001 through ADR-006) must be followed as specified
- Responsibility boundaries: auth in `accounts` app, proposals in `proposals` app, shared config in `config`
- `@admin_required` decorator (or `AdminRequiredMixin`) must be the single point of admin authorization enforcement — authorization logic must not be duplicated in individual views
- No inline `is_staff` checks in view body without going through the decorator/mixin

### Technical Constraints

- Python 3.12+, Django 5.2.1, PostgreSQL 16, gunicorn 23.0.0, whitenoise 6.7.0, psycopg[binary] 3.2.4 (as specified in Section 15 of basic design)
- Exact package versions must be pinned at implementation time using `pip freeze` or equivalent; do not use floating ranges
- No JavaScript framework or frontend build pipeline — Django templates only
- `django.contrib.admin` must remain excluded from `INSTALLED_APPS`
- Single `config/settings.py` — no separate dev/prod settings files

### Security Constraints

- Sensitive data must never be logged (proposal body, submitter fields, passwords, session tokens)
- Generic login error message only: `"Invalid email address or password."`
- Constant-time dummy hash in `EmailBackend` when email not found (as specified in Section 6.1)
- All admin views must use `@admin_required` or `AdminRequiredMixin` — no exceptions
- `{% csrf_token %}` required in all POST forms including the logout form
- `.env` must be in `.gitignore`; no secrets committed to the repository
- `SESSION_COOKIE_SECURE = False` only (BD-01 accepted for localhost-only trial)

### Operational Constraints

- The application must start cleanly with `docker compose up` after `docker compose down` (data preserved in `pgdata` volume)
- `docker compose down --volumes` must be documented as destructive in `.env.example` comments or README
- The backup script `scripts/backup.sh` must be executable (`chmod +x`) and must handle the case where no backup files exist yet (no rotation error on first run)

---

## 8. Related ADRs

### Related ADRs

- ADR-001: Authentication Strategy — email + password, session-based, EmailBackend, HTTP-only cookie
- ADR-002: Authorization Model — `is_staff=True`, `@admin_required` decorator
- ADR-003: Technology Stack — Django 5.x, PostgreSQL 16, Docker Compose, Django templates, pytest
- ADR-004: Database Persistence and Docker Compose — named `pgdata` volume, `./backups` bind mount, `.env` secrets
- ADR-005: Audit Log Policy — append-only `StatusHistory` and `AdminLoginLog`, atomic status change, sensitive data prohibition
- ADR-006: Data Retention and Operational Deletion — GPG AES-256 backup encryption, 14-generation rotation

### ADR Compliance Notes

All implementation decisions are already made and recorded in these ADRs. The Builder must implement exactly what is specified without deviating from the ADR decisions. If a conflict arises between the basic design and an ADR, stop and report before proceeding.

### ADR Required?

- [x] No new ADR required — all architectural decisions are made and accepted

---

## 9. Forbidden Changes

AI must not:

- change unrelated files
- rewrite large parts of the system outside the approved scope
- introduce new libraries not listed in Section 15 of the basic design without reporting it as a deviation
- add `django.contrib.admin` to `INSTALLED_APPS`
- implement proposal deletion at any layer
- implement login lockout or rate limiting (out of scope)
- add comments, filter, or sort to the admin proposal list
- use floating package version ranges (e.g., `Django>=5.0`) — all versions must be pinned
- commit secrets (`.env`, real credentials) to the repository
- skip `{% csrf_token %}` in any POST form
- implement an inline `is_staff` check in a view body without going through the `@admin_required` decorator or `AdminRequiredMixin`
- write sensitive data (proposal body, submitter fields, passwords, session tokens) to any log
- call `.update()` or `.delete()` on `StatusHistory` or `AdminLoginLog` querysets
- use `on_delete=CASCADE` on `StatusHistory.proposal` or `StatusHistory.changed_by` (must be `PROTECT`)
- perform status change and `StatusHistory` creation outside of `transaction.atomic()`
- decide task completion by itself

---

## 10. Task Breakdown

The implementation must be divided into the following small reviewable units. Each unit must be independently reviewable. Do not mix units.

### Expected Work Units

- [ ] Unit 1: Project scaffold
  - Create `miniimpbox/` repository root with `config/`, `proposals/`, `accounts/` app packages
  - `manage.py`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `.gitignore`, `requirements.txt`
  - `config/settings.py` (all settings as specified, including WhiteNoise, session, logging)
  - `config/urls.py` with all three includes (proposals, accounts, proposals_admin)
  - Verify `docker compose up` starts and `manage.py check` passes

- [ ] Unit 2: Data models and migrations
  - `proposals/models.py`: `Proposal`, `StatusHistory` (with `PROTECT` FKs, Meta ordering)
  - `accounts/models.py`: `AdminLoginLog`
  - Run `makemigrations` and `migrate`; verify all tables created correctly
  - No test code in this unit; model unit tests added in Unit 6

- [ ] Unit 3: Authentication — EmailBackend, session settings, seed_admin
  - `accounts/backends.py`: `EmailBackend` with timing-attack mitigation
  - `AUTHENTICATION_BACKENDS` in settings already set in Unit 1; verify it's correct
  - `accounts/management/commands/seed_admin.py`
  - Verify `seed_admin` creates an `is_staff=True` user from `.env` credentials
  - Initial login/logout views stub (GET only) to verify routing — full views in Unit 4

- [ ] Unit 4: Account views — AdminLoginView, AdminLogoutView, AdminLoginLog write
  - Full `AdminLoginView` (GET + POST): authenticate, write `AdminLoginLog`, session creation, redirect
  - `AdminLogoutView` (POST only): session invalidation, redirect
  - `accounts/urls.py`: login and logout routes
  - `accounts/templates/accounts/login.html`: login form with `{% csrf_token %}`
  - All login attempts (success and failure) must write to `AdminLoginLog` before response

- [ ] Unit 5: Authorization decorator and mixin
  - `accounts/decorators.py`: `admin_required` decorator
  - `AdminRequiredMixin` for class-based views
  - Unit tests: unauthenticated access → redirect to login; non-staff → 403; staff → pass through

- [ ] Unit 6: Public proposal submission
  - `proposals/forms.py`: `ProposalForm` with all validation rules (title 1-100, body 1-2000, submitter_contact email format if non-empty)
  - `ProposalSubmitView` (GET + POST), `ProposalSubmitCompleteView` (GET)
  - `proposals/urls.py`: submit and submit_complete routes
  - Templates: `base.html`, `proposals/submit.html`, `proposals/submit_complete.html`
  - Unit tests: valid submission, each invalid field case

- [ ] Unit 7: Admin proposal views
  - `proposals/forms.py`: `StatusChangeForm`
  - `AdminProposalListView` (GET, paginated 20/page, `@admin_required`)
  - `AdminProposalDetailView` (GET, `@admin_required`)
  - `AdminStatusChangeView` (POST, `@admin_required`, `@require_POST`, atomic status change + `StatusHistory` write)
  - `proposals/admin_urls.py`: list, detail, status_change routes
  - Templates: `proposals/admin_list.html`, `proposals/admin_detail.html`, `proposals/admin_status_change.html`
  - Unit tests: status change atomicity, invalid status rejection, `StatusHistory` row verification

- [ ] Unit 8: Backup script
  - `scripts/backup.sh` with GPG AES-256 encryption and 14-generation rotation
  - Verify script is executable; verify rotation logic handles zero existing files
  - Document in `.env.example` that `BACKUP_GPG_PASSPHRASE` must be set and stored separately

- [ ] Unit 9: Test coverage and verification
  - Ensure all High-risk test areas from Section 20 of basic design have test coverage
  - Create `docs/tests/miniimpbox_v1_test_cases.csv` with test case records
  - Run full test suite; all tests must pass
  - Create `docs/tests/coverage_result.csv` for High-risk modules

### AI Instructions for Task Splitting

Work through units in order. Each unit must pass its own verification before moving to the next. Report the outcome of each unit before proceeding. Do not skip units or merge units without explaining why.

---

## 11. Required Tests

Testing must follow `docs/ai-development/policies/TEST_POLICY.md`.

### Required Validation

- [x] Lint validation (flake8 or ruff)
- [x] Existing test execution after each unit
- [x] New tests for all new behavior
- [x] Manual verification procedure definition
- [x] Test case CSV created: `docs/tests/miniimpbox_v1_test_cases.csv`
- [x] Coverage result CSV created: `docs/tests/coverage_result.csv`

### Test-First Required?

- [x] Yes — for all High-risk items (authentication, authorization, status change atomicity, sensitive data prohibition, audit log)

Test-first means: write the test, confirm it fails, implement the feature, confirm the test passes.

### Test Case CSV

Required test case file: `docs/tests/miniimpbox_v1_test_cases.csv`

Must be created and updated as units are completed. Covers all test areas listed in Section 20 of the basic design, including:

- Proposal submission (valid and each invalid case)
- Login success, login failure (wrong credentials, non-existent email)
- Logout
- Unauthenticated admin access (each admin URL)
- Non-staff admin access
- Status change (valid, invalid status value)
- `StatusHistory` append-only (no update/delete paths)
- Sensitive data prohibition in logs and audit tables

### Coverage Result CSV

Required coverage file: `docs/tests/coverage_result.csv`

Must track coverage for High-risk modules: `accounts/backends.py`, `accounts/views.py`, `accounts/models.py`, `proposals/views.py` (admin views), `proposals/models.py`, `proposals/forms.py`.

### Required Test Perspectives

- Normal cases (valid input, expected flow)
- Error cases (invalid input, form errors, 404, 403)
- Boundary conditions (field length limits, empty optional fields)
- Permission differences (unauthenticated, authenticated non-staff, authenticated staff)
- Data consistency (status change + StatusHistory atomicity, rollback on failure)
- Append-only constraint (no update/delete paths exist)
- Sensitive data non-disclosure (proposal body/submitter fields not in logs or audit tables)

---

## 12. Manual Verification

### Manual Verification Required?

- [x] Yes

### Manual Verification Steps

After all units are complete and all automated tests pass, perform the following manual verification steps using the running Docker Compose stack:

**Setup:**
1. `cp .env.example .env` — edit with real secret values (do not commit)
2. `docker compose up -d`
3. `docker compose exec app python manage.py seed_admin`

**Public proposal submission:**
1. Open `http://localhost:8000/` — verify proposal form renders
2. Submit with all fields (title, body, submitter_name, submitter_contact) — verify redirect to `/submit/complete/`
3. Submit with title and body only (optional fields empty) — verify success
4. Submit with invalid submitter_contact (e.g., `not-an-email`) — verify form error, no submission
5. Submit with body exceeding 2000 characters — verify form error, no submission

**Admin authentication:**
1. Open `http://localhost:8000/admin-portal/login/` — verify login form renders
2. Login with incorrect credentials — verify generic error message `"Invalid email address or password."`, verify `AdminLoginLog` row written (success=False)
3. Login with correct credentials — verify redirect to `/admin-portal/`, verify `AdminLoginLog` row written (success=True)
4. Access `/admin-portal/` directly (unauthenticated, new browser session) — verify redirect to login

**Admin portal:**
1. Navigate to admin proposal list — verify submitted proposals appear, paginated at 20/page
2. Click a proposal — verify detail view with status history
3. Change proposal status — verify new status shown, `StatusHistory` row visible in detail view
4. Attempt an invalid status change (direct POST with invalid value) — verify proposal unchanged, no history row
5. Logout (POST) — verify redirect to login, verify subsequent admin URL access redirects to login

**Security spot checks:**
1. Open `http://localhost:8000/admin-portal/` in a fresh session (no cookie) — must redirect to login
2. Log in as a user with `is_staff=False` (create manually via shell) — access `/admin-portal/` — must return HTTP 403
3. Verify Django admin at `/admin/` is not accessible (404 or similar — it must not be routed)

### Required Human Checks

- [x] Business correctness (proposal submission and admin portal behavior)
- [x] User-facing behavior (form rendering, error messages, redirects)
- [x] Permission checks (unauthenticated redirect, non-staff 403)
- [x] Error handling (form errors, 404, generic auth error)
- [x] Security spot checks (session isolation, CSRF protection on forms)

---

## 13. Completion Conditions

This task is ready for human review only when:

- [x] Implementation is limited to the approved scope (no out-of-scope features)
- [x] Forbidden changes were not made
- [x] All accepted ADRs (ADR-001 through ADR-006) were followed
- [x] Lint validation passes
- [x] All automated tests pass
- [x] Test case CSV is created: `docs/tests/miniimpbox_v1_test_cases.csv`
- [x] Coverage result CSV is created: `docs/tests/coverage_result.csv`
- [x] Manual verification steps are documented (above)
- [x] Remaining risks are documented
- [x] Assumptions are documented
- [x] An implementation record is created under `docs/implementation/`

AI must not write "Task complete" or "Implementation complete." The correct phrasing is: "Ready for human review — final completion requires human verification."

---

## 14. Expected Output from AI

### 1. Summary

After completing all units, provide:
- What was implemented (per unit)
- What was not implemented (any deviations from scope)
- What decisions were made during implementation (assumptions)

### 2. Files Changed

List all created files with a one-line description per file.

### 3. Scope Compliance

Confirm that all in-scope items were implemented and no out-of-scope items were added.

### 4. ADR Compliance

Confirm compliance with each of ADR-001 through ADR-006. Flag any deviations or concerns.

### 5. Tests and Validation

| Check | Result | Notes |
|---|---|---|
| Lint | Pass / Fail | Notes |
| All tests | Pass / Fail / Count | Notes |
| Test case CSV | Created | Path |
| Coverage CSV | Created | Path |
| Implementation record | Created | Path |

### 5.1 Review / Gate Evidence

| Evidence | Result | Notes |
|---|---|---|
| Implementation Reviewer | Performed / Not performed | Outcome |
| Human gate decision (BD-02) | Pending | Non-blocking for development; must be resolved before trial start |

### 6. Manual Verification Procedure

As defined in Section 12 of this request.

### 7. Remaining Risks

At minimum, report on:
- BD-02: `ip_address` logging — confirm before trial start
- Any deviations from basic design discovered during implementation
- Any package version changes made (explain why if any version was updated)

### 8. Assumptions

List all implementation-time assumptions made that are not already in the basic design.

### 9. Recommended Next Actions

After implementation review is complete:
1. Human performs manual verification (Section 12)
2. Human resolves BD-02 (IP address logging)
3. Define trial end date and document operational deletion procedure (ADR-006)
4. Test backup restore procedure before trial start (ADR-004)
5. Set calendar reminder for retention period end (trial end date + 90 days)

### 10. Human Review Required

> Final completion must be determined by human review, required tests, and manual verification.

---

## 15. AI Pre-Implementation Checklist

Before implementation, AI must verify:

- [x] Purpose is clear — build Mini Improvement Box v1 as specified in approved basic design
- [x] Scope is clear — all components listed in Section 4
- [x] Out-of-scope items are defined — Section 5
- [x] Requirements are concrete enough to test — Section 6 + requirements-v1.md
- [x] Constraints and forbidden changes are clear — Sections 7 and 9
- [x] Related ADRs are identified — Section 8 (ADR-001 through ADR-006)
- [x] No new ADR is required — all architectural decisions are made
- [x] Task is broken into small reviewable units — Section 10 (Units 1-9)
- [x] Test-first is required for High-risk items — Section 11
- [x] Required tests and manual verification are defined — Sections 11 and 12

---

## References

| Document | Path | Status |
|---|---|---|
| Requirements | `docs/requirements/requirements-v1.md` | Approved 2026-05-11 |
| Basic Design | `docs/design/basic-design-v1.md` | Approved 2026-05-11 |
| ADR-001 | `docs/adr/ADR-001-authentication-strategy.md` | Accepted 2026-05-11 |
| ADR-002 | `docs/adr/ADR-002-authorization-model.md` | Accepted 2026-05-11 |
| ADR-003 | `docs/adr/ADR-003-technology-stack.md` | Accepted 2026-05-11 |
| ADR-004 | `docs/adr/ADR-004-database-persistence-and-docker-compose.md` | Accepted 2026-05-11 |
| ADR-005 | `docs/adr/ADR-005-audit-log-policy.md` | Accepted 2026-05-11 |
| ADR-006 | `docs/adr/ADR-006-data-retention-and-operational-deletion.md` | Accepted 2026-05-11 |
| Test Policy | `docs/ai-development/policies/TEST_POLICY.md` | — |
| Security Policy | `docs/ai-development/policies/SECURITY_POLICY.md` | — |
| Implementation Workflow | `docs/ai-development/workflows/IMPLEMENTATION_WORKFLOW.md` | — |
