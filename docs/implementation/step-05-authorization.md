# Implementation Record — Step 5: @admin_required decorator and AdminRequiredMixin

## Metadata

| Field | Value |
|---|---|
| Roadmap step | Phase 2, Step 5 — @admin_required decorator and AdminRequiredMixin |
| Implementation request | docs/implementation/implementation-request-v1.md |
| Roadmap | docs/design/roadmap-v1.md |
| Date | 2026-05-12 |
| Builder | AI Builder (Claude, Cowork mode) |
| Risk classification | **High** — authorization enforcement (Phase 2) |
| TDD required | Yes — all acceptance criteria |
| Status | Pending Implementation Reviewer sign-off |

---

## 1. Scope

Step 5 implements the `@admin_required` decorator, `AdminRequiredMixin` for CBVs, and applies the decorator to the `_stub_list` view in `proposals/admin_urls.py`.

**In scope (per roadmap-v1.md Step 5):**

- `accounts/decorators.py`: `admin_required` decorator (wraps `@login_required` + `is_staff` check → `PermissionDenied`) and `AdminRequiredMixin` (same logic for CBVs via `AccessMixin`)
- `proposals/admin_urls.py`: `@admin_required` applied to `_stub_list` stub view
- `accounts/tests/test_decorators.py`: 8 TDD tests (written before implementation)
- `docs/tests/miniimpbox_v1_test_cases.csv`: rows S5-1 through S5-9 added

**Out of scope (deferred to later steps):**

- Real `AdminProposalListView`, `AdminProposalDetailView`, `AdminStatusChangeView` (Step 7 — will use `@admin_required` / `AdminRequiredMixin`)
- Public proposal submission (Step 6)

---

## 2. Changed Files

| File | Action | Rationale |
|---|---|---|
| `accounts/decorators.py` | Created | `admin_required` decorator and `AdminRequiredMixin` per basic design Section 7.2 and ADR-002 |
| `proposals/admin_urls.py` | Updated | Applied `@admin_required` to `_stub_list`; added import; Step 4 Finding R2 (R-STUB) resolved |
| `accounts/tests/test_decorators.py` | Created | 8 TDD tests written before implementation |
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated | Rows S5-1 through S5-9 added |

---

## 3. Implementation Notes and Assumptions

**SD-01 (Assumption): Decorator composition in `admin_required`**

The `admin_required` decorator uses `@login_required(login_url='/admin-portal/login/')` applied to the inner `wrapped_view`. The `@wraps(view_func)` preserves the function metadata. Flow: `login_required` handles unauthenticated redirects; the inner `wrapped_view` handles the `is_staff` check → `PermissionDenied` for authenticated non-staff. This matches the basic design Section 7.2 code exactly.

**SD-02 (Assumption): `AdminRequiredMixin.dispatch()` uses explicit two-step check**

- If not authenticated: `handle_no_permission()` (from `AccessMixin`) → redirects to `login_url`. Django's `AccessMixin` redirects when `raise_exception=False` and user is not authenticated.
- If authenticated but not staff: `raise PermissionDenied` directly → HTTP 403.
- This matches the decorator behavior and the ADR-002 requirement.

**SD-03 (Assumption): Mixin tests use `RequestFactory`, not `Client`**

`AdminRequiredMixin` is tested directly via `RequestFactory` to avoid needing a real URL registration for the test CBV. This allows independent testing of the mixin behavior. For `PermissionDenied` cases, `RequestFactory` tests use `pytest.raises(PermissionDenied)` rather than checking HTTP 403, since there is no Django exception handler in the `RequestFactory` pipeline. This is correct: the `Client`-based decorator tests verify HTTP 403 end-to-end.

**SD-04 (Assumption): Step 4 Finding R2 (R-STUB) resolved**

Step 4 Implementation Reviewer Finding R2 flagged that `_stub_list` had no `@admin_required`. Step 5 resolves this by applying `@admin_required` to `_stub_list`. The risk `R-STUB` from the Step 4 implementation record is now mitigated.

**SD-05 (Assumption): TDD Red→Green sequence**

Tests were written first. Red phase: 7/8 failures (1 trivial pass — `test_staff_authenticated_proceeds_to_view` with no decorator on stub yet returned 200 for staff, which is the correct eventual behavior). Green phase: 8/8 passed after implementation.

---

## 4. Checks Run

| Check | Result | Notes |
|---|---|---|
| TDD Red phase — 7/8 failures before implementation | Confirmed | 1 trivial pass: staff access to unprotected stub already returned 200 |
| TDD Green phase — 8/8 pass after implementation | Pass | `8 passed in 2.10s` |
| Full test suite (63 tests) — regression check | Pass | `63 passed in 21.22s` — no regressions |
| Static review of `decorators.py` against basic design Section 7.2 | Pass | Decorator matches design code exactly; Mixin follows same logic |
| Static review of `proposals/admin_urls.py` | Pass | `@admin_required` applied; import present |
| ADR compliance review | Pass | See Section 10 |
| Security review | Pass | See Section 6 (Reviewer) |
| Lint (flake8/ruff) | Not run | Not installed in Docker image; deferred to Step 9 |
| CI | Not configured | Not configured for this project |

---

## 5. Test Case CSV Status

| File | Status |
|---|---|
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated — rows S5-1 through S5-9 added |

**S5-1 through S5-8** (Automated, TDD): All Pass — 8 tests passed in Docker. Version/Commit: Working tree (update to commit hash post-commit).
**S5-9** (Human, Phase-blocking Gate 2): Pending — requires browser-level verification after all Phase 2 steps complete.

**Coverage CSV:** Not created in Step 5. High-risk module coverage measured in Step 9.

---

## 6. Implementation Reviewer Outcome

**Reviewer:** AI Implementation Reviewer (Claude, Cowork mode) — independent of Builder

**Review date:** 2026-05-12

### Scope reviewed

- `accounts/decorators.py`
- `proposals/admin_urls.py` (updated)
- `accounts/tests/test_decorators.py`
- `docs/tests/miniimpbox_v1_test_cases.csv` rows S5-1 through S5-9
- Implementation record Sections 1–5
- Compliance against: basic design Section 7.2, ADR-002, SECURITY_POLICY.md

### Findings

**Finding R1 — Non-blocking — Step 4 Finding R2 (R-STUB) resolved**

Step 4 Implementation Reviewer Finding R2 flagged that `_stub_list` had no `@admin_required`. Step 5 applies `@admin_required` to `_stub_list`. Unauthenticated access to `/admin-portal/proposals/` now correctly redirects to login; non-staff access returns HTTP 403. Finding R2/R-STUB from Step 4 is resolved.

Classification: Non-blocking (informational — confirms Step 4 risk R-STUB is now mitigated).

**Finding R2 — Non-blocking — `AdminRequiredMixin` not yet applied to any real CBV**

`AdminRequiredMixin` is implemented and tested but not yet applied to any production CBV (Step 7 will apply it). The current only admin view is the function-based `_stub_list` using `@admin_required`. This is the correct state for Step 5 — the mixin is ready for Step 7 use.

Classification: Non-blocking (informational — by design; Step 7 applies mixin to real views).

### Behavior compliance review

| Acceptance criterion | Implementation | Match |
|---|---|---|
| Unauthenticated → redirect to `/admin-portal/login/?next=<url>` (decorator) | `@login_required(login_url='/admin-portal/login/')` handles this | ✓ |
| Authenticated non-staff → HTTP 403 (decorator) | `if not request.user.is_staff: raise PermissionDenied` | ✓ |
| Authenticated is_staff=True → proceeds to view (decorator) | Falls through to `view_func(request, *args, **kwargs)` | ✓ |
| Unauthenticated → redirect to login (mixin) | `handle_no_permission()` called for anonymous user | ✓ |
| Authenticated non-staff → PermissionDenied (mixin) | `raise PermissionDenied` in dispatch | ✓ |
| Authenticated is_staff=True → proceeds (mixin) | `super().dispatch()` called | ✓ |

### Security review

- `@admin_required` correctly requires BOTH authentication AND `is_staff=True` ✓
- Unauthenticated users are redirected (not shown 403) — correct per ADR-002 UX ✓
- Non-staff authenticated users receive 403 (PermissionDenied) — correct per ADR-002 ✓
- `login_url` set to `/admin-portal/login/` in both decorator and mixin — prevents fallback to Django admin login ✓
- No sensitive data exposed by decorator/mixin themselves ✓
- Decorator uses `@wraps(view_func)` — preserves function identity for URL reversal and debugging ✓

### Test adequacy review

All 4 acceptance criteria from roadmap Step 5 are covered by automated tests. Both decorator (via `_stub_list` URL) and mixin (via `RequestFactory`) are tested independently. The non-staff HTTP 403 case is tested via Client for the decorator and via `pytest.raises(PermissionDenied)` for the mixin — both are correct for their respective test contexts.

### Overall finding

**No blocking findings.** Both findings are non-blocking. Step 5 is ready to commit.

---

## 7. Tester Outcome

**Tester used:** Yes — AI Tester (Claude, Cowork mode), independent of Builder.

**Tester review date:** 2026-05-12

**Rationale:** Step 5 is High-risk (authorization enforcement). IMPLEMENTATION_WORKFLOW.md requires a separate Tester for High-risk steps.

### Tester assessment

**Test coverage assessment**

1. **Decorator tests via `_stub_list` URL (S5-1 through S5-4)** — All four acceptance criteria (unauthenticated redirect, redirect includes next, non-staff 403, staff 200) are tested end-to-end via the real URL. This exercises the full Django request pipeline including `SessionMiddleware` and exception handling. Correct approach for decorator verification.

2. **Mixin tests via `RequestFactory` (S5-5 through S5-8)** — The mixin is tested independently of any URL registration. Anonymous user redirect, next parameter, non-staff PermissionDenied, and staff proceed are all verified. Using `pytest.raises(PermissionDenied)` for the mixin non-staff test is correct: `RequestFactory` does not run Django's exception handling middleware, so the raw exception is tested.

3. **Redirect URL correctness** — Both decorator and mixin tests verify that the `Location` header contains `/admin-portal/login/` (not Django's default `/accounts/login/`). This confirms `login_url` is correctly set.

4. **`next` parameter presence** — Both decorator and mixin tests verify `next=` is present in the redirect Location. This confirms `?next=<url>` behavior required by the roadmap.

**Missing test perspectives considered:**

- **`next` parameter value correctness:** Tests verify `next=` is present and the URL contains `admin-portal/proposals/` for the decorator. The exact URL encoding is not checked, which is acceptable — the presence of `next=` and the target URL path is sufficient.
- **Staff user POST to protected view:** Only GET is tested. POST behavior is equivalent since `@admin_required` wraps the entire view function. Acceptable — GET verification is sufficient for authorization boundary testing.
- **Concurrent/multiple requests:** Not tested. Not required for this unit-level authorization test.

**Tester verdict:** All High-risk acceptance criteria are covered. No additional tests required. Implementation is ready for commit from a testing perspective.

---

## 8. Human Verification Items

| ID | Item | Classification | Status |
|---|---|---|---|
| HV-S5-1 | Manual browser: access `/admin-portal/proposals/` without session — verify redirect to login with `?next=` parameter (S5-9) | Phase-blocking (Gate 2) | Pending |

**Gate note:** Human Gate 2 items require Steps 3, 4, and 5 all to be complete. Step 5 is the final Phase 2 step. Gate 2 must be cleared before Phase 3 begins. Gate 2 covers: Steps 3+4+5 end-to-end auth flow, `_stub_list` access control, Django `/admin/` inaccessibility.

---

## 9. Assumptions and Remaining Risks

| ID | Type | Description |
|---|---|---|
| SD-01 | Assumption | Decorator composition: `@login_required` outer + `is_staff` inner per basic design Section 7.2 |
| SD-02 | Assumption | `AdminRequiredMixin.dispatch()` two-step: not-authenticated → `handle_no_permission()`, authenticated non-staff → `raise PermissionDenied` |
| SD-03 | Assumption | Mixin tests use `RequestFactory`; non-staff case uses `pytest.raises(PermissionDenied)` |
| SD-04 | Assumption | Step 4 Finding R2 (R-STUB) resolved by applying `@admin_required` to `_stub_list` |
| SD-05 | Assumption | TDD Red→Green confirmed in Docker (7/8 red, 8/8 green) |
| BD-02 | Risk | ip_address in AdminLoginLog — remains pending; non-blocking for development; release-blocking for trial start |
| R-LINT | Risk | Lint not run; deferred to Step 9 |

---

## 10. ADR Compliance Notes

| ADR | Compliance |
|---|---|
| ADR-001 | N/A for Step 5 (auth mechanism unchanged) |
| ADR-002 | `is_staff=True` as admin identifier; `@admin_required` and `AdminRequiredMixin` implemented; applied to `_stub_list`; unauthenticated → redirect; authenticated non-staff → 403 ✓ |
| ADR-003 | Django decorator pattern and `AccessMixin`; no new dependencies ✓ |
| ADR-004 | N/A for Step 5 |
| ADR-005 | N/A for Step 5 |
| ADR-006 | N/A for Step 5 |

---

## 11. Commit Hash

**Commit:** Pending

---

## 12. Push Status

**Status:** Pending commit and push.

**Gate check:** Step 5 is the last step of Phase 2. Human Gate 2 must be cleared before Phase 3 (Step 6) begins. Gate 2 does not block the push of Step 5 — it blocks the start of Phase 3. Push may proceed after commit.

---

*This implementation record is produced by the AI Builder. It is traceability evidence, not final acceptance, residual risk acceptance, or release approval.*
