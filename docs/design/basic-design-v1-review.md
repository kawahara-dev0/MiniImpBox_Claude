# Design Review — Basic Design v1

## Metadata

| Field | Value |
|---|---|
| Artifact reviewed | docs/design/basic-design-v1.md |
| Review date | 2026-05-11 |
| Reviewer | AI Design Reviewer (Claude, Cowork mode) |
| Policies applied | REVIEW_POLICY.md, SECURITY_POLICY.md, BASIC_DESIGN_CHECKLIST.md |
| Requirements basis | docs/requirements/requirements-v1.md (Approved) |
| ADR basis | ADR-001 through ADR-006 (All Accepted) |

---

## Overall Judgment

**Acceptable with concerns — workflow must stop for BD-01 (session cookie security acceptance) before implementation begins.**

The basic design is comprehensive, internally consistent, and correctly resolves all items deferred from the six accepted ADRs. Architecture is simple and appropriate for a limited internal trial. Security baselines are correctly applied. One structural auto-fixable finding (URL routing inconsistency) and one clarification auto-fixable finding were resolved during this review pass.

One phase-blocking human-decision item (BD-01: `SESSION_COOKIE_SECURE`) must be resolved before implementation begins. BD-02 (IP address logging) is non-blocking for development but release-blocking for trial start.

---

## BASIC_DESIGN_CHECKLIST Assessment

| Section | Status | Notes |
|---|---|---|
| 1. Requirement Understanding | ✓ Pass | Scope, out-of-scope, failure cases, and NFRs all addressed |
| 2. Users and Responsibility | ✓ Pass | Two-tier role model clear; admin authority limited to `is_staff` |
| 3. Data and Business Rules | ✓ Pass | PROTECT FKs, append-only audit tables, atomic status change |
| 4. Security and Risk Awareness | ✓ Pass | Auth, authz, sensitive data, error messages all addressed; BD-01 flagged |
| 5. Failure Handling and Operational Risk | ✓ Pass | Error handling table, named volumes, `.env` secrets management |
| 6. Architecture and Responsibility Boundaries | ✓ Pass | Layers clear; auth ownership in single decorator; ADR compliance table present |
| 7. Critical Verification Strategy | ✓ Pass | Section 20 lists test areas by risk level with test-first recommendation |
| 8. Release and Business Impact | ✓ Pass | Trial/production separation explicit; BD-01 and BD-02 classified correctly |

---

## What the Designer did well

- All six ADR-deferred items are fully resolved with concrete, implementable decisions: `EmailBackend` for email-based auth, `is_staff` for admin identification, GPG AES-256 for backup encryption, named `pgdata` Docker volume, single `config/settings.py` for trial, `proposals.admin_urls` + `accounts.urls` routing.
- `transaction.atomic()` wrapping the status update and `StatusHistory` insert is explicitly specified — the atomicity requirement from ADR-005 is correctly implemented in the design.
- The sensitive data prohibition (proposal body, submitter fields, passwords, session tokens must not appear in logs) is consistently reiterated in the data model notes, logging settings, and audit log sections.
- `on_delete=models.PROTECT` on `StatusHistory` is the correct choice: it prevents accidental deletion of proposals or admins that have history records, and it is consistent with the no-application-deletion requirement (HD-10).
- The `EmailBackend.authenticate()` includes a constant-time dummy hash (`User().set_password(password)`) when the email is not found, mitigating timing-based account enumeration.
- BD-01 is correctly classified as phase-blocking and BD-02 as non-blocking (development) / release-blocking (trial start).
- The project structure splits public and admin concerns into `proposals.urls` and `proposals.admin_urls`, with authentication concerns in `accounts`.
- Django admin (`django.contrib.admin`) is excluded from `INSTALLED_APPS`, not merely unregistered from URLs — the stronger and correct choice.

---

## Auto-fixable findings (this round — all resolved)

1. **URL routing inconsistency (structural):** `config/urls.py` originally only routed to `proposals.urls` and `accounts.urls`, but admin proposal paths (`/admin-portal/proposals/...`) were listed under `proposals/urls.py` without a corresponding routing prefix. This would result in admin proposal URLs being inaccessible at their intended paths. Fixed by separating `proposals/urls.py` (public, rooted at `/`) from `proposals/admin_urls.py` (admin proposals, included under `/admin-portal/proposals/` in `config/urls.py`). URL namespace `proposals_admin` added. *(Fixed)*

2. **`django.contrib.admin` exclusion ambiguity:** The original text said "excluded from `INSTALLED_APPS` **or** its URL is not registered" — ambiguous. Fixed to: excluded from `INSTALLED_APPS` entirely, with a note that this also prevents creation of `django_admin_log` and `Permission` tables. *(Fixed)*

3. **Document History:** Updated to record the two auto-fixable fixes above. *(Fixed)*

No further auto-fixable findings remain.

---

## Human-decision findings

### HDF-01: BD-01 — `SESSION_COOKIE_SECURE = False` (Phase-blocking security acceptance)

The basic design sets `SESSION_COOKIE_SECURE = False` for the Docker Compose trial environment, which runs over HTTP. This means session cookies will be transmitted in plaintext over the network if the application is accessed from any machine other than localhost.

This setting is acceptable **only if** the trial application is accessed exclusively via localhost (`http://localhost:8000` or `http://127.0.0.1:8000`). If the host machine is accessed over a LAN, VPN, or any network connection, session tokens can be intercepted.

**Action required:** Human confirms one of the following:
- A. The trial will be accessed via localhost only → accept `SESSION_COOKIE_SECURE = False` as-is.
- B. The trial will be accessed over a network → HTTPS must be configured before the trial begins, and `SESSION_COOKIE_SECURE = True` must be set.

This is a security risk acceptance decision. AI cannot make this decision.

### HDF-02: Basic design approval itself (primary finding — workflow must stop)

The document is a draft. It must be approved by a human before implementation begins.

---

## Missing or Excessive Artifacts

- No implementation request yet. Correct — basic design must be approved before implementation requests are drafted.
- No test case CSV yet. Correct — the verification strategy in Section 20 identifies test areas; test cases will be written during implementation.
- The operational deletion procedure (ADR-006 Notes) is not yet documented. This is a pre-trial requirement but does not block basic design approval or implementation start.

---

## Security Review Notes

- **Authentication**: `EmailBackend` correctly queries by `email`, uses `check_password()`, includes timing-attack mitigation for non-existent accounts. ✓
- **Session**: HTTP-only cookie, SameSite=Lax, 8h + browser-close expiry. `SESSION_COOKIE_SECURE=False` is the only open risk (BD-01). ✓ pending BD-01
- **Authorization**: `@admin_required` decorator centralizes `is_staff` check + `login_required`. All admin views must use it — this is a critical implementation requirement that must be verified in code review. ✓ (design)
- **CSRF**: `CsrfViewMiddleware` in MIDDLEWARE, `{% csrf_token %}` required in all POST forms including logout. ✓
- **Error messages**: Login failure returns generic message; 404 uses Django default; no internal details exposed. ✓
- **Sensitive data logging**: Prohibition stated in model notes, settings LOGGING config, and audit log section. Must be verified in implementation review. ✓ (design)
- **Password handling**: Django default PBKDF2-SHA256, hashed by `create_user()`. Never logged. ✓
- **Secrets**: All via `.env`; `.env.example` committed; `.gitignore` required; backup passphrase separate from backup files. ✓

---

## Data Review Notes

- `StatusHistory` and `AdminLoginLog` are append-only; this is stated in model Notes and Section 9. Must be enforced in code review (no `update()`/`delete()` on these models). ✓
- `transaction.atomic()` for status change + history write ensures atomicity. ✓
- `on_delete=models.PROTECT` on `StatusHistory.proposal` and `StatusHistory.changed_by`: prevents accidental cascade deletion. ✓
- `submitter_contact` stored as plain `CharField`, not `EmailField` at model level, to prevent incidental re-validation of existing data during migrations. ✓

---

## Recommended Next Action

1. **Human resolves BD-01** (session cookie security — localhost-only vs. network access). Record the decision in the document (Section 10, BD-01 row) and update `SESSION_COOKIE_SECURE` if needed.
2. **Human approves `basic-design-v1.md`** and records approval in document metadata (Approver field, Status field, Document History).
3. After approval, draft an implementation request using `docs/ai-development/templates/IMPLEMENTATION_REQUEST_TEMPLATE.md` or `IMPLEMENTATION_REQUEST_SHORT_TEMPLATE.md`, referencing this basic design and the six accepted ADRs.
4. Before the trial begins: define the trial end date, document the operational deletion procedure (ADR-006), and test the backup restore procedure (ADR-004).

---

## Human Verification Required

### Phase-blocking

- **BD-01** must be resolved (session cookie security acceptance) before implementation begins.
- **Human must approve `basic-design-v1.md`** before implementation begins.

### Non-blocking

- BD-02 (IP address logging) may be confirmed during development without blocking implementation start.
- `LANGUAGE_CODE` and `TIME_ZONE` (set to `'ja'` / `'Asia/Tokyo'` in Assumption BD-A-07) may be adjusted before trial without design change.

### Release-blocking

- BD-02 (IP address logging) must be confirmed before trial start.
- Operational deletion procedure must be documented and reviewed before trial start (ADR-006).
- Backup restore test must be performed before relying on backups (ADR-004).
- `SESSION_COOKIE_SECURE = True` and HTTPS required before any production use.

---

## Final Note

Final completion must be determined by human review, required tests, and manual verification.

This design artifact is ready for human review.

---

## Current Review Result

**Outcome: Acceptable with concerns — workflow must stop for BD-01 security acceptance and overall basic design approval.**

All ADR-deferred items are correctly resolved. Auto-fixable findings (3 items) are resolved. No policy violations. The only blocking items are BD-01 (session cookie security acceptance decision) and overall human approval of the basic design.
