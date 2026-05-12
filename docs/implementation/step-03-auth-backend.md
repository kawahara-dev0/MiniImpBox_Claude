# Implementation Record — Step 3: EmailBackend and seed_admin

## Metadata

| Field | Value |
|---|---|
| Roadmap step | Phase 2, Step 3 — EmailBackend, session settings, seed_admin management command |
| Implementation request | docs/implementation/implementation-request-v1.md |
| Roadmap | docs/design/roadmap-v1.md |
| Date | 2026-05-12 |
| Builder | AI Builder (Claude, Cowork mode) |
| Risk classification | **High** — authentication logic (Phase 2) |
| TDD required | Yes — all acceptance criteria |
| Status | Pending Implementation Reviewer sign-off |

---

## 1. Scope

Step 3 implements the email-based authentication backend and the admin seed management command.

**In scope (per roadmap-v1.md Step 3):**

- `accounts/backends.py`: `EmailBackend` — query by email, constant-time dummy hash for non-existent accounts, `check_password()` + `user_can_authenticate()`
- `accounts/management/__init__.py`, `accounts/management/commands/__init__.py`: package markers
- `accounts/management/commands/seed_admin.py`: read `DJANGO_ADMIN_EMAIL` and `DJANGO_ADMIN_PASSWORD` from environment, create `is_staff=True`, `is_superuser=False` user; idempotent
- `accounts/tests/test_backends.py`: 8 TDD tests for EmailBackend
- `accounts/tests/test_management.py`: 6 TDD tests for seed_admin
- `docs/tests/miniimpbox_v1_test_cases.csv`: rows S3-1 through S3-14 added

**Settings already correct from Step 1 (no change required):**

- `AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']` — confirmed present in `config/settings.py`

**Out of scope (deferred to later steps):**

- `AdminLoginView`, `AdminLogoutView`, `AdminLoginLog` write (Step 4)
- `@admin_required` decorator and mixin (Step 5)
- Any view, URL, or template (Steps 4–7)

---

## 2. Changed Files

| File | Action | Rationale |
|---|---|---|
| `accounts/backends.py` | Created | EmailBackend per basic design Section 6.1 and ADR-001 |
| `accounts/management/__init__.py` | Created | Python package marker for management module |
| `accounts/management/commands/__init__.py` | Created | Python package marker for commands module |
| `accounts/management/commands/seed_admin.py` | Created | seed_admin management command per basic design Section 6.6 and ADR-001 |
| `accounts/tests/test_backends.py` | Created | 8 TDD tests for EmailBackend (written before implementation) |
| `accounts/tests/test_management.py` | Created | 6 TDD tests for seed_admin (written before implementation) |
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated | Rows S3-1 through S3-14 added |

---

## 3. Implementation Notes and Assumptions

**SC-01 (Assumption): TDD sequence**
Tests were written first. Docker confirmed import error (Red) before implementation, then 14/14 Pass (Green) after implementation.

**SC-02 (Assumption): `User().set_password(password)` for timing mitigation**
The basic design Section 6.1 specifies this exact pattern. It creates a temporary User instance and calls `set_password()` to execute the PBKDF2 hash, equalizing execution time between "email not found" and "email found but wrong password" paths. This prevents an attacker from enumerating valid email addresses via response timing.

**SC-03 (Assumption): `AUTHENTICATION_BACKENDS` already set**
`config/settings.py` already contains `AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']` from Step 1. No settings change is required in Step 3. Confirmed by AI review (test case S3-14).

**SC-04 (Assumption): management/__init__.py files**
`accounts/management/__init__.py` and `accounts/management/commands/__init__.py` are required Python package markers. Not listed explicitly in the roadmap but required for Django to discover the management command. No business behavior is affected.

**SC-05 (Assumption): Separate Tester used**
Step 3 is High-risk (authentication). A separate AI Tester review is included in Section 7 per the IMPLEMENTATION_WORKFLOW.md requirement.

---

## 4. Checks Run

| Check | Result | Notes |
|---|---|---|
| TDD Red phase — import error before implementation | Confirmed | `ModuleNotFoundError: No module named 'accounts.backends'` |
| TDD Green phase — 14/14 tests pass | Pass | `14 passed in 7.07s` |
| Full test suite (32 tests) — regression check | Pass | `32 passed in 8.09s` — no regressions |
| Static review of `backends.py` against basic design Section 6.1 | Pass | EmailBackend matches design exactly |
| Static review of `seed_admin.py` against basic design Section 6.6 | Pass | Command matches design exactly |
| ADR-001 compliance review | Pass | See Section 10 |
| Security review | Pass | See Section 6 (Reviewer) |
| Lint (flake8/ruff) | Not run | Not installed in Docker image; deferred to Step 9 |
| CI | Not configured | Not configured for this project |

---

## 5. Test Case CSV Status

| File | Status |
|---|---|
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated — rows S3-1 through S3-14 added |

**S3-1 through S3-13** (Automated, TDD): All Pass — 14 tests passed in Docker.
**S3-14** (AI review): Pass — `AUTHENTICATION_BACKENDS` confirmed correct in `config/settings.py`.

**Coverage CSV:** Not created in Step 3. High-risk module coverage will be measured in Step 9.

---

## 6. Implementation Reviewer Outcome

**Reviewer:** AI Implementation Reviewer (Claude, Cowork mode) — independent of Builder

**Review date:** 2026-05-12

### Scope reviewed

- `accounts/backends.py`, `accounts/management/commands/seed_admin.py`
- `accounts/tests/test_backends.py`, `accounts/tests/test_management.py`
- `docs/tests/miniimpbox_v1_test_cases.csv` rows S3-1 through S3-14
- Implementation record Sections 1–5
- Compliance against: basic design Section 6.1 and 6.6, ADR-001, SECURITY_POLICY.md

### Findings

**Finding R1 — Non-blocking — `User().set_password()` dummy hash: password=None edge case**

If `password=None` is passed (e.g., a malformed request), `User().set_password(None)` is still called. Django's `set_password(None)` sets an unusable password (no hash computed), making the dummy hash meaningless for timing if `password is None`. However, this is an edge case that cannot produce a valid login under any circumstances. The `check_password(None)` call on a real user would also fail immediately. Timing risk is negligible for this edge case. No code change required.

Classification: Non-blocking. Documented for awareness.

**Finding R2 — Non-blocking — `seed_admin` reads env vars at runtime, not at import**

`os.environ['DJANGO_ADMIN_EMAIL']` is read in `handle()`, not at module load time. This is the correct pattern — env vars are guaranteed to be available at command execution time. No issue.

Classification: Non-blocking (informational).

**Finding R3 — Non-blocking — `test_wrong_email_runs_dummy_hash_for_timing_mitigation` patches `User.set_password`**

The test patches `User.set_password` on the class to verify the dummy hash call. This is appropriate for verifying the timing mitigation pattern. The patch scope is limited to the test duration. No interaction with production behavior.

Classification: Non-blocking (test design note).

### Code-level compliance review

**`EmailBackend.authenticate()`**

| Item | Design spec | Implementation | Match |
|---|---|---|---|
| Query by email | `User.objects.get(email=username)` | `User.objects.get(email=username)` | ✓ |
| DoesNotExist → dummy hash | `User().set_password(password); return None` | `User().set_password(password); return None` | ✓ |
| Wrong password → None | `check_password()` fails → return None | `check_password()` fails → return None | ✓ |
| Inactive user → None | `user_can_authenticate()` returns False | Inherited from `ModelBackend`; tested and confirmed | ✓ |
| Extends `ModelBackend` | Yes | `class EmailBackend(ModelBackend)` | ✓ |

**`seed_admin` command**

| Item | Design spec | Implementation | Match |
|---|---|---|---|
| Read email from env | `os.environ['DJANGO_ADMIN_EMAIL']` | `os.environ['DJANGO_ADMIN_EMAIL']` | ✓ |
| Read password from env | `os.environ['DJANGO_ADMIN_PASSWORD']` | `os.environ['DJANGO_ADMIN_PASSWORD']` | ✓ |
| Idempotent check | `filter(email=email).exists()` | `filter(email=email).exists()` | ✓ |
| `is_staff=True` | Yes | Yes | ✓ |
| `is_superuser=False` | Yes | Yes | ✓ |
| `username = email` | Yes | Yes | ✓ |
| Hashed password | `create_user(password=password)` | `create_user(password=password)` | ✓ |

### Security review

- Password is hashed via Django's `create_user()` — never stored in plaintext ✓
- Password never appears in any `stdout.write()` call ✓
- Email address not used to construct a user-facing error message ✓
- Dummy hash executed for non-existent accounts (constant-time mitigation) ✓
- `user_can_authenticate()` enforces `is_active=True` check ✓
- No credential is logged anywhere in Step 3 code ✓
- `AUTHENTICATION_BACKENDS` setting is already correctly scoped to `EmailBackend` only ✓
- Django admin (`contrib.admin`) remains excluded from `INSTALLED_APPS` ✓

### Test adequacy review

| Required acceptance criterion | Test(s) | Status |
|---|---|---|
| authenticate() returns None for wrong email (after dummy hash) | S3-3, S3-4 | Covered ✓ |
| authenticate() returns None for wrong password | S3-2 | Covered ✓ |
| authenticate() returns user for correct credentials | S3-1 | Covered ✓ |
| Timing mitigation (dummy hash called) | S3-4 | Covered ✓ |
| seed_admin: is_staff=True, is_superuser=False | S3-8 | Covered ✓ |
| seed_admin: no duplicate on second run | S3-12 | Covered ✓ |
| seed_admin: username = email | S3-9 | Covered ✓ |
| seed_admin: password hashed | S3-10 | Covered ✓ |
| Additional: end-to-end (seed + authenticate) | S3-11 | Covered ✓ |
| Additional: inactive user → None | S3-5 | Covered ✓ |
| Additional: empty/None username → None | S3-6 | Covered ✓ |
| Additional: no exception leaked | S3-7 | Covered ✓ |

All acceptance criteria are covered. The TDD approach (Red→Green confirmed) provides strong correctness evidence for High-risk authentication code.

### Overall finding

**No blocking findings.** All three findings are non-blocking. Step 3 is ready to commit.

The TDD approach was correctly applied. Timing mitigation is verified by the `patch.object` test. Seed command is idempotent and idempotency is test-confirmed. Security policy requirements are met.

---

## 7. Tester Outcome

**Tester used:** Yes — AI Tester (Claude, Cowork mode), independent of Builder.

**Tester review date:** 2026-05-12

**Rationale for using Tester:** Step 3 is classified as High-risk (authentication logic, Phase 2). IMPLEMENTATION_WORKFLOW.md requires a separate Tester for authentication work.

### Tester assessment

**Test coverage assessment**

The test suite covers all required acceptance criteria from roadmap Step 3 plus additional security edge cases. Key observations:

1. **Timing mitigation test (S3-4)** — Correctly uses `patch.object(User, 'set_password')` to verify the dummy hash call rather than attempting to measure actual timing (which would be unreliable in automated tests). This is the correct approach for verifying this security property.

2. **Inactive user test (S3-5)** — Tests `user_can_authenticate()` behavior by creating an `is_active=False` user. Correctly exercises the `ModelBackend.user_can_authenticate()` inheritance path.

3. **No account-existence leak tests (S3-3, S3-7)** — Both the "returns None" and "no exception" properties are tested independently. Good separation of concerns.

4. **End-to-end seed + authenticate test (S3-11)** — Verifies the integration between `seed_admin` and `EmailBackend`, confirming that the seed procedure produces credentials that work with the custom backend.

**Missing test perspectives considered and accepted:**

- **Timing attack resistance (actual time measurement):** Cannot be reliably tested in unit tests due to process scheduling variability. The `set_password` call verification (S3-4) is the appropriate automated substitute.
- **Concurrent seed_admin calls (race condition):** Not tested. Acceptable for a single-admin management command on an internal trial system. Not a blocking gap.
- **`os.environ` key missing (KeyError):** If `DJANGO_ADMIN_EMAIL` or `DJANGO_ADMIN_PASSWORD` is not set, `seed_admin` will raise `KeyError`. This is an operator error, not a testable application bug. Acceptable behavior — the operator must set env vars before running.

**Test adequacy judgment:** Adequate for a High-risk authentication step. Test-first evidence is recorded (Red phase confirmed before implementation).

**Tester verdict:** No additional tests required. Implementation is ready for commit from a testing perspective.

---

## 8. Human Verification Items

| ID | Item | Classification | Status |
|---|---|---|---|
| HV-S3-1 | End-to-end `seed_admin` + login flow via browser (Gate 2 item) | Phase-blocking (Gate 2) | Pending |
| HV-S3-2 | Confirm `AdminLoginLog` write on login (Gate 2 item — Step 4 required first) | Phase-blocking (Gate 2) | Pending |

**Gate note:** Human Gate 2 (End-to-end authentication verification) covers Steps 3, 4, and 5. It cannot be cleared until Steps 4 and 5 are also implemented and reviewed.

---

## 9. Assumptions and Remaining Risks

| ID | Type | Description |
|---|---|---|
| SC-01 | Assumption | TDD sequence confirmed — Red before implementation, Green after |
| SC-02 | Assumption | `User().set_password()` dummy hash: timing mitigation per basic design Section 6.1 |
| SC-03 | Assumption | `AUTHENTICATION_BACKENDS` already correct from Step 1; no settings change needed |
| SC-04 | Assumption | `management/__init__.py` files added as required Python package markers |
| SC-05 | Assumption | Separate AI Tester used per High-risk classification |
| BD-02 | Risk | ip_address in AdminLoginLog — remains pending; non-blocking for development; release-blocking for trial start |
| R-LINT | Risk | Lint not run; deferred to Step 9 |
| R-TIMING | Risk | Actual timing difference between paths not measured in automated tests (inherently unreliable); mitigation verified via `set_password` call assertion |
| R-BRUTE | Risk | No failed login lockout in v1 — documented in basic design Section 6.4; acceptable for internal trial |

---

## 10. ADR Compliance Notes

| ADR | Compliance |
|---|---|
| ADR-001 | EmailBackend authenticates by email, not username; session settings set in Step 1; dummy hash for timing mitigation; seed_admin creates is_staff=True, is_superuser=False user; password hashed by Django ✓ |
| ADR-002 | N/A for Step 3 (no authorization decorator yet — Step 5) |
| ADR-003 | Django's built-in ModelBackend subclassed; no new dependencies ✓ |
| ADR-004 | N/A for Step 3 |
| ADR-005 | No audit log write in Step 3 (AdminLoginLog write is Step 4); no sensitive data logged ✓ |
| ADR-006 | N/A for Step 3 |

---

## 11. Commit Hash

**Commit:** `63e7f72`

---

## 12. Push Status

**Status:** Pending push.

**Gate check:** Step 3 is in Phase 2. Human Gate 2 covers Steps 3, 4, and 5, and must be cleared before Phase 3 begins. Gate 2 does not block the push of Step 3 — it blocks the start of Phase 3. Push may proceed after commit.

---

*This implementation record is produced by the AI Builder. It is traceability evidence, not final acceptance, residual risk acceptance, or release approval.*
