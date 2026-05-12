# Implementation Record — Step 4: AdminLoginView, AdminLogoutView, AdminLoginLog write

## Metadata

| Field | Value |
|---|---|
| Roadmap step | Phase 2, Step 4 — Account views: AdminLoginView, AdminLogoutView, AdminLoginLog write |
| Implementation request | docs/implementation/implementation-request-v1.md |
| Roadmap | docs/design/roadmap-v1.md |
| Date | 2026-05-12 |
| Builder | AI Builder (Claude, Cowork mode) |
| Risk classification | **High** — authentication views + audit logging (Phase 2) |
| TDD required | Yes — all acceptance criteria |
| Status | Pending Implementation Reviewer sign-off |

---

## 1. Scope

Step 4 implements the admin login/logout views, URLs, templates, and the AdminLoginLog audit write.

**In scope (per roadmap-v1.md Step 4):**

- `accounts/views.py`: `AdminLoginView` (GET + POST) and `AdminLogoutView` (POST only with `@require_POST`)
- `accounts/urls.py`: replaced placeholder — `accounts:login` and `accounts:logout` patterns
- `accounts/templates/accounts/login.html`: login form with `{% csrf_token %}`, email, password fields, error display
- `templates/base.html`: shared base template (minimal HTML structure)
- `proposals/admin_urls.py`: added `_stub_list` placeholder view + `name='list'` entry to allow `proposals_admin:list` reverse resolution (required for login redirect; replaced by real view in Step 7)
- `accounts/tests/test_views.py`: 23 TDD tests (written before implementation)
- `docs/tests/miniimpbox_v1_test_cases.csv`: rows S4-1 through S4-17 added

**Out of scope (deferred to later steps):**

- `@admin_required` decorator and mixin (Step 5)
- Admin proposal list/detail/status views (Step 7)
- Public proposal form (Step 6)

---

## 2. Changed Files

| File | Action | Rationale |
|---|---|---|
| `accounts/views.py` | Created | AdminLoginView, AdminLogoutView per basic design Section 5.3 and 9.2 |
| `accounts/urls.py` | Updated | Replaced Step 1 placeholder — accounts:login and accounts:logout per basic design Section 4.4 |
| `accounts/templates/accounts/login.html` | Created | Login form per basic design Section 8.3 |
| `templates/base.html` | Created | Shared base template per basic design Section 2 (minimal structure) |
| `proposals/admin_urls.py` | Updated | Added `_stub_list` view + `name='list'` to allow `proposals_admin:list` reverse; replaced by real view in Step 7 |
| `accounts/tests/test_views.py` | Created | 23 TDD tests written before implementation |
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated | Rows S4-1 through S4-17 added |

---

## 3. Implementation Notes and Assumptions

**SD-01 (Assumption): `_stub_list` in proposals/admin_urls.py**
`AdminLoginView` redirects to `proposals_admin:list` on successful login. This URL name requires an entry in `proposals/admin_urls.py`. A temporary stub view (`_stub_list`) was added to allow the reverse resolution. This stub is replaced by the real `AdminProposalListView` in Step 7. The stub returns HTTP 200 with a placeholder body.

**SD-02 (Assumption): TDD sequence**
Tests were written first. Red phase confirmed (21/23 failures before implementation; the 2 passing tests were trivial no-session checks unaffected by missing views). Green phase: 23/23 passed after implementation + stub.

**SD-03 (Assumption): `_get_client_ip` in views.py**
Helper function per basic design Section 9.2. Reads `HTTP_X_FORWARDED_FOR` first (for reverse proxy setups), falls back to `REMOTE_ADDR`. ip_address stored in AdminLoginLog (BD-02 pending).

**SD-04 (Assumption): `@method_decorator(require_POST, name='dispatch')` for AdminLogoutView**
Django's `require_POST` decorator returns HTTP 405 for non-POST methods. Applied via `method_decorator` on the class-based view.

**SD-05 (Assumption): No CSRF enforcement issue in tests**
Django's test `Client` enforces CSRF by default only in `enforce_csrf_checks=True` mode. Tests use the default client (CSRF checks disabled) to simplify test setup. Real browser POST will include CSRF token from the login form. No security weakness introduced.

---

## 4. Checks Run

| Check | Result | Notes |
|---|---|---|
| TDD Red phase — 21/23 failures before implementation | Confirmed | Expected failures from missing views/URLs |
| TDD Green phase — 23/23 pass after implementation | Pass | `23 passed in 11.79s` |
| Full test suite (55 tests) — regression check | Pass | `55 passed in 19.38s` — no regressions |
| Static review of `views.py` against basic design Section 5.3 and 9.2 | Pass | All behavior matches design |
| Static review of `login.html` against basic design Section 8.3 | Pass | CSRF token, email, password fields present |
| Static review of `accounts/urls.py` against basic design Section 4.4 | Pass | accounts:login, accounts:logout paths correct |
| ADR compliance review | Pass | See Section 10 |
| Security review | Pass | See Section 6 (Reviewer) |
| Lint (flake8/ruff) | Not run | Not installed in Docker image; deferred to Step 9 |
| CI | Not configured | Not configured for this project |

---

## 5. Test Case CSV Status

| File | Status |
|---|---|
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated — rows S4-1 through S4-17 added |

**S4-1 through S4-14** (Automated, TDD): All Pass — 23 tests passed in Docker.
**S4-15 through S4-17** (Human, Phase-blocking Gate 2): Pending — require browser-level verification after Step 5 is complete.

**Coverage CSV:** Not created in Step 4. High-risk module coverage measured in Step 9.

---

## 6. Implementation Reviewer Outcome

**Reviewer:** AI Implementation Reviewer (Claude, Cowork mode) — independent of Builder

**Review date:** 2026-05-12

### Scope reviewed

- `accounts/views.py`, `accounts/urls.py`, `accounts/templates/accounts/login.html`, `templates/base.html`
- `proposals/admin_urls.py` (stub addition)
- `accounts/tests/test_views.py`
- `docs/tests/miniimpbox_v1_test_cases.csv` rows S4-1 through S4-17
- Implementation record Sections 1–5
- Compliance against: basic design Sections 5.3, 8.3, 9.2, ADR-001, ADR-005, SECURITY_POLICY.md

### Findings

**Finding R1 — Non-blocking — `Reviewer Finding R1` from step-01-scaffold.md: `LOGIN_REDIRECT_URL` not used**

This finding was flagged in Step 1: `LOGIN_REDIRECT_URL = '/admin-portal/'` in settings.py points to a URL that doesn't match any pattern exactly. The Step 4 implementation correctly does NOT rely on `LOGIN_REDIRECT_URL` — `AdminLoginView.post()` explicitly redirects to `reverse('proposals_admin:list')`. Finding R1 from Step 1 is now resolved in practice.

Classification: Non-blocking (informational — confirms Step 1 Reviewer Finding R1 is resolved).

**Finding R2 — Non-blocking — `_stub_list` in proposals/admin_urls.py**

The stub view returns HTTP 200 with a plaintext body and has no authentication check. This is intentional and temporary — unauthenticated access to `/admin-portal/proposals/` would currently succeed (no `@admin_required`). This is acceptable because:
1. The stub is explicitly documented as a placeholder for Step 7.
2. Step 5 adds `@admin_required` to the real view in Step 7.
3. No sensitive data is served by the stub.

Classification: Non-blocking. Flag for Step 5/7 Builder to replace stub with real view + `@admin_required`.

**Finding R3 — Non-blocking — `ip_address` stored as-supplied from `get_client_ip()`**

`ip_address` is populated from `HTTP_X_FORWARDED_FOR` or `REMOTE_ADDR` without validation beyond what Django's `GenericIPAddressField` provides on save. In a Docker Compose localhost setup, `REMOTE_ADDR` will be `127.0.0.1` or the container network IP. `X-Forwarded-For` is not expected in this setup. Acceptable for v1 trial.

Classification: Non-blocking.

### Behavior compliance review

| Acceptance criterion | Implementation | Match |
|---|---|---|
| GET renders login form | `AdminLoginView.get()` renders `accounts/login.html` | ✓ |
| GET already-staff redirects to list | Check `request.user.is_authenticated and request.user.is_staff` | ✓ |
| POST correct: AdminLoginLog success=True | `AdminLoginLog.objects.create(success=True)` before login() | ✓ |
| POST correct: session created | `login(request, user)` called | ✓ |
| POST correct: redirect to proposals_admin:list | `redirect('proposals_admin:list')` | ✓ |
| POST incorrect: AdminLoginLog success=False | `AdminLoginLog.objects.create(success=False)` on auth failure | ✓ |
| POST incorrect: no session | `login()` not called on failure | ✓ |
| POST incorrect: generic error message | `'Invalid email address or password.'` in context | ✓ |
| Log written BEFORE response | `AdminLoginLog.create()` before `redirect()` or `render()` | ✓ |
| password never in AdminLoginLog | Only `email`, `success`, `ip_address` stored; no password field | ✓ |
| POST logout: session invalidated | `logout(request)` called | ✓ |
| POST logout: redirect to accounts:login | `redirect('accounts:login')` | ✓ |
| GET logout: HTTP 405 | `@require_POST` via `method_decorator` | ✓ |

### Security review

- `{% csrf_token %}` in login.html ✓
- `logout()` called on POST logout (server-side session flush) ✓
- Password not stored, logged, or passed anywhere in views.py ✓
- Error message is generic; no account existence revealed ✓
- `AdminLoginLog` written before response (cannot be skipped by exception after log) ✓
- `AdminLoginView.get()` does not expose sensitive data ✓
- `_get_client_ip()` reads standard headers only; no shell injection risk ✓
- `require_POST` prevents CSRF-based logout via GET ✓

### Test adequacy review

All 13 acceptance criteria from roadmap Step 4 are covered by automated tests. Additional edge cases covered: already-authenticated redirect, unauthenticated logout, CSRF token presence, non-existent email behavior matching wrong-password behavior (FR-AUTH-05).

### Overall finding

**No blocking findings.** All three findings are non-blocking. Step 4 is ready to commit.

---

## 7. Tester Outcome

**Tester used:** Yes — AI Tester (Claude, Cowork mode), independent of Builder.

**Tester review date:** 2026-05-12

**Rationale:** Step 4 is High-risk (authentication views + audit logging). IMPLEMENTATION_WORKFLOW.md requires a separate Tester.

### Tester assessment

**Test coverage assessment**

1. **AdminLoginLog sensitive data tests (S4-6, S4-11)** — Two separate tests verify password absence: one for successful login and one for failed login. Both check all three stored columns (email, success, ip_address). Correct approach.

2. **`test_login_log_written_before_response_on_failure` (S4-10)** — Verifies the audit-before-response ordering. The implementation places `AdminLoginLog.objects.create()` before the `login()`/`render()` call. The test confirms the log exists after a failed POST. This is the correct way to verify ordering in a unit test context.

3. **`test_nonexistent_email_shows_same_generic_error` (S4-9)** — Explicitly tests FR-AUTH-05 non-disclosure for non-existent email. Same error message as wrong-password case confirmed.

4. **`test_get_logout_returns_405` (S4-13)** — Verifies POST-only enforcement. Critical for preventing CSRF-based logout via GET link.

**Missing test perspectives considered:**

- **CSRF enforcement in POST tests:** Tests use Django test client with CSRF disabled. Real-browser CSRF behavior is correct (token in form, CsrfViewMiddleware enabled). No test gap — this is standard Django test practice.
- **`X-Forwarded-For` header in ip_address:** Not tested. Acceptable for Step 4; tested manually in Gate 2 if needed.
- **Non-staff authenticated user accessing login page:** GET redirect is only for `is_staff=True`. Non-staff authenticated user would see the login form (re-render). Not explicitly tested. Low risk — no sensitive data exposed.

**Tester verdict:** All High-risk acceptance criteria are covered. No additional tests required. Implementation is ready for commit from a testing perspective.

---

## 8. Human Verification Items

| ID | Item | Classification | Status |
|---|---|---|---|
| HV-S4-1 | Manual browser login with correct credentials — verify AdminLoginLog + session + redirect (S4-15) | Phase-blocking (Gate 2) | Pending |
| HV-S4-2 | Manual browser login with wrong credentials — verify generic error + AdminLoginLog success=False (S4-16) | Phase-blocking (Gate 2) | Pending |
| HV-S4-3 | Manual browser logout — verify session invalidated + redirect (S4-17) | Phase-blocking (Gate 2) | Pending |
| HV-S4-4 | Verify `/admin/` (Django admin) is not reachable (Gate 2 item) | Phase-blocking (Gate 2) | Pending |

**Gate note:** Human Gate 2 items require Steps 3, 4, and 5 all to be complete and working end-to-end. Gate 2 must be cleared before Phase 3 begins.

---

## 9. Assumptions and Remaining Risks

| ID | Type | Description |
|---|---|---|
| SD-01 | Assumption | _stub_list in proposals/admin_urls.py — temporary; replaced in Step 7 by real AdminProposalListView with @admin_required |
| SD-02 | Assumption | TDD Red→Green confirmed in Docker |
| SD-03 | Assumption | _get_client_ip reads X-Forwarded-For / REMOTE_ADDR per basic design Section 9.2 |
| SD-04 | Assumption | @require_POST via method_decorator for AdminLogoutView |
| SD-05 | Assumption | Django test client has CSRF disabled by default — no security gap in test setup |
| BD-02 | Risk | ip_address in AdminLoginLog — remains pending; non-blocking for development; release-blocking for trial start |
| R-STUB | Risk | _stub_list has no @admin_required — unauthenticated access to /admin-portal/proposals/ currently allowed; mitigated in Step 5/7 |
| R-LINT | Risk | Lint not run; deferred to Step 9 |

---

## 10. ADR Compliance Notes

| ADR | Compliance |
|---|---|
| ADR-001 | AdminLoginView uses authenticate() + login(); AdminLogoutView uses logout(); session invalidated on logout; redirect to proposals_admin:list on success ✓ |
| ADR-002 | N/A for Step 4 auth views themselves; @admin_required applied in Step 5 |
| ADR-003 | Django CBVs used; no new dependencies ✓ |
| ADR-004 | N/A for Step 4 |
| ADR-005 | AdminLoginLog written before response; password never stored; email, success, ip_address only ✓ |
| ADR-006 | N/A for Step 4 |

---

## 11. Commit Hash

**Status:** Pending — will be updated after commit.

---

## 12. Push Status

**Status:** Pending.

**Gate check:** Step 4 is in Phase 2. Human Gate 2 covers Steps 3–5 end-to-end. Gate 2 does not block push of this step — it blocks the start of Phase 3. Push may proceed after commit.

---

*This implementation record is produced by the AI Builder. It is traceability evidence, not final acceptance, residual risk acceptance, or release approval.*
