# Implementation Record — Step 7: Admin Proposal Views and Status Change

## Metadata

| Field | Value |
|---|---|
| Roadmap step | Phase 3, Step 7 — Admin proposal views and status change |
| Implementation request | docs/implementation/implementation-request-v1.md |
| Roadmap | docs/design/roadmap-v1.md |
| Date | 2026-05-12 |
| Builder | AI Builder (Claude, Cowork mode) |
| Risk classification | **High** — status change atomicity + audit log integrity (Phase 3) |
| TDD required | Yes — status change atomicity and sensitive data non-disclosure |
| Status | Pending Implementation Reviewer sign-off |

---

## 1. Scope

Step 7 implements the admin proposal list, detail, and status change views, replacing the `_stub_list` placeholder from Steps 4/5.

**In scope (per roadmap-v1.md Step 7):**

- `proposals/forms.py`: `StatusChangeForm` added
- `proposals/views.py`: `AdminProposalListView` (GET, paginated), `AdminProposalDetailView` (GET, 404 on missing), `AdminStatusChangeView` (POST only — enforced by View method dispatch, atomic status change + StatusHistory write)
- `proposals/admin_urls.py`: replaced `_stub_list` stub with real URL patterns (`list`, `detail`, `status_change`)
- `proposals/templates/proposals/admin_list.html`: proposal list with pagination and logout button (English UI)
- `proposals/templates/proposals/admin_detail.html`: proposal detail with status change form and history table (English UI)
- `proposals/tests/test_views_admin.py`: 29 TDD tests (written before implementation — Red 19/29 failures, Green 29/29)
- `docs/tests/miniimpbox_v1_test_cases.csv`: rows S7-1 through S7-19 added

**Out of scope:**

- Backup script (Step 8)
- Test coverage CSV (Step 9)

---

## 2. Changed Files

| File | Action | Rationale |
|---|---|---|
| `proposals/forms.py` | Updated | Added `StatusChangeForm` per basic design Section 8.2 |
| `proposals/views.py` | Updated | Added `AdminProposalListView`, `AdminProposalDetailView`, `AdminStatusChangeView` per basic design Section 5.2 and 9.1 |
| `proposals/admin_urls.py` | Updated | Replaced `_stub_list` stub — `list`, `detail`, `status_change` patterns per basic design Section 4.3 |
| `proposals/templates/proposals/admin_list.html` | Committed in Step 6 | Already present; English UI, pagination, logout |
| `proposals/templates/proposals/admin_detail.html` | Committed in Step 6 | Already present; English UI, status change form, history table |
| `proposals/tests/test_views_admin.py` | Created | 29 TDD tests (written before implementation) |
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated | Rows S7-1 through S7-19 added |

---

## 3. Implementation Notes and Assumptions

**SD-01 (Assumption): `AdminStatusChangeView` uses `View` method dispatch for POST-only enforcement**

Only `post()` is defined on `AdminStatusChangeView`. Django's `View` returns HTTP 405 for methods not defined. This achieves the "POST only" requirement from the roadmap without `@require_POST`. The `AdminRequiredMixin` checks authentication/authorization before Django's method dispatch routes to `post()`, so:
- Unauthenticated GET → redirect to login (from `AdminRequiredMixin.dispatch()`)
- Authenticated non-staff GET → PermissionDenied (403) (from `AdminRequiredMixin.dispatch()`)
- Authenticated staff GET → HTTP 405 (from `View` method dispatch)

**SD-02 (Assumption): Atomic status change per basic design Section 9.1**

`transaction.atomic()` wraps both `proposal.save(update_fields=['status', 'updated_at'])` and `StatusHistory.objects.create(...)`. If either fails, both are rolled back. The atomicity test (`test_both_proposal_and_history_updated_atomically`) verifies the positive case: after a successful POST, both proposal.status and StatusHistory exist.

**SD-03 (Assumption): Invalid status redirect to detail with `?error=invalid_status`**

Per basic design Section 11: "redirect back to detail with `?error=invalid_status`". `AdminStatusChangeView.post()` redirects to `/admin-portal/proposals/<pk>/?error=invalid_status` on form validation failure. The detail template shows an error message when `error == 'invalid_status'`.

**SD-04 (Assumption): `AdminStatusChangeView` uses `AdminRequiredMixin`, not `@admin_required`**

All admin CBVs use `AdminRequiredMixin` (consistent with Step 7 role as CBV-based views). This is equivalent to `@admin_required` for function-based views per basic design Section 7.2.

**SD-05 (Assumption): TDD Red→Green sequence**

Tests written first. Red phase: 19/29 failures (10 trivial passes for model field checks and URL-routing-level 404/403 behaviors). Green phase: 29/29 passed after implementation.

**SD-06 (Assumption): `_stub_list` removed from `proposals/admin_urls.py`**

The stub (added in Step 4, protected in Step 5) is replaced by `AdminProposalListView`. The Step 5 TDD tests (`TestAdminRequiredDecorator`) tested via the stub URL `/admin-portal/proposals/`. These tests continue to pass because `AdminProposalListView` uses `AdminRequiredMixin` which provides equivalent authorization behavior.

---

## 4. Checks Run

| Check | Result | Notes |
|---|---|---|
| TDD Red phase — 19/29 failures before implementation | Confirmed | 10 trivial passes (model field checks, URL-routing 404/403) |
| TDD Green phase — 29/29 pass after implementation | Pass | `29 passed in 9.43s` |
| Full test suite (119 tests) — regression check | Pass | `119 passed in 29.65s` — no regressions |
| Static review of `views.py` against basic design Section 5.2 and 9.1 | Pass | All admin view behaviors match design; atomicity implemented correctly |
| Static review of `admin_urls.py` against basic design Section 4.3 | Pass | list, detail, status_change patterns correct |
| Static review of `StatusChangeForm` against basic design Section 8.2 | Pass | `ChoiceField(choices=Proposal.STATUS_CHOICES)` — invalid values rejected |
| Sensitive data non-disclosure: StatusHistory has no body/submitter_name/submitter_contact | Pass | Confirmed by 4 TDD tests (S7-14) |
| ADR compliance review | Pass | See Section 10 |
| Security review | Pass | See Section 6 (Reviewer) |
| Lint (flake8/ruff) | Not run | Not installed in Docker image; deferred to Step 9 |
| CI | Not configured | Not configured for this project |

---

## 5. Test Case CSV Status

| File | Status |
|---|---|
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated — rows S7-1 through S7-19 added |

**S7-1 through S7-15** (Automated, TDD): All Pass — 29 tests passed in Docker. Version/Commit: Working tree (updated to commit hash post-commit).
**S7-16 through S7-19** (Human, Phase-blocking Gate 3): Pending — require browser-level functional verification.

**Coverage CSV:** Not created in Step 7. High-risk module coverage measured in Step 9.

---

## 6. Implementation Reviewer Outcome

**Reviewer:** AI Implementation Reviewer (Claude, Cowork mode) — independent of Builder

**Review date:** 2026-05-12

### Scope reviewed

- `proposals/forms.py` (StatusChangeForm), `proposals/views.py` (admin views), `proposals/admin_urls.py`
- `proposals/templates/proposals/admin_list.html`, `admin_detail.html`
- `proposals/tests/test_views_admin.py`
- `docs/tests/miniimpbox_v1_test_cases.csv` rows S7-1 through S7-19
- Implementation record Sections 1–5
- Compliance against: basic design Sections 4.3, 5.2, 8.2, 9.1, 11, ADR-002, ADR-005, SECURITY_POLICY.md

### Findings

**Finding R1 — Non-blocking — `AdminStatusChangeView` GET returns 405 for authenticated staff**

`AdminStatusChangeView` defines only `post()`. Authenticated staff making a GET to `/admin-portal/proposals/<pk>/status/` receive HTTP 405 (Method Not Allowed), not a redirect or 404. This is correct: the URL is POST-only per design, and 405 is the appropriate response. Unauthenticated and non-staff requests are still handled by `AdminRequiredMixin` before method dispatch. No security gap.

Classification: Non-blocking (informational — expected behavior, documents correctly in SD-01).

**Finding R2 — Non-blocking — No append-only enforcement test for `.update()`/`.delete()` on StatusHistory**

Basic design Section 9.3 says: "Application code must never call `.update()`, `.delete()`, or `.filter(...).delete()` on `StatusHistory` or `AdminLoginLog` querysets." A grep-based test confirming no such calls in application code is not present. The roadmap notes this for Step 9 (coverage CSV). Acceptable deferral.

Classification: Non-blocking. Flag for Step 9 to add grep-based check or explicit test.

### Behavior compliance review

| Acceptance criterion | Implementation | Match |
|---|---|---|
| GET list: proposals ordered by -created_at, 20/page | `Proposal.objects.all()` + `Paginator(qs, 20)` — Model Meta ordering is `-created_at` | ✓ |
| GET detail: proposal + StatusHistory + StatusChangeForm | `get_object_or_404`, `status_history.all()`, `StatusChangeForm()` in context | ✓ |
| POST status_change valid: update + StatusHistory in atomic() | `transaction.atomic()` wraps both writes | ✓ |
| POST status_change valid: redirect to detail | `redirect('proposals_admin:detail', pk=pk)` | ✓ |
| POST status_change invalid: proposal unchanged + no StatusHistory | `StatusChangeForm` validation fails before DB write | ✓ |
| sensitive fields not in StatusHistory | Only old_status, new_status, proposal, changed_by, changed_at stored | ✓ |
| Unauthenticated → redirect to login | `AdminRequiredMixin` handles all admin views | ✓ |
| Non-staff → HTTP 403 | `AdminRequiredMixin` raises `PermissionDenied` | ✓ |
| Nonexistent pk → 404 | `get_object_or_404(Proposal, pk=pk)` | ✓ |

### Security review

- All admin views use `AdminRequiredMixin` — no unauthenticated or non-staff access ✓
- `transaction.atomic()` prevents partial audit log state ✓
- `StatusHistory` stores only `old_status`, `new_status`, `proposal` FK, `changed_by` FK, `changed_at` ✓
- `body`, `submitter_name`, `submitter_contact` never passed to `StatusHistory.objects.create()` ✓
- Invalid status value rejected by `StatusChangeForm.ChoiceField` ✓
- Error message on invalid status does not expose internals ✓
- `{% csrf_token %}` in both admin templates ✓

### Test adequacy review

All roadmap acceptance criteria for status change atomicity and sensitive data non-disclosure are covered by TDD tests (S7-10 through S7-14). Authorization boundary tests (unauthenticated, non-staff) are covered for all three views. The positive atomicity test verifies that both writes succeed together. The negative test (invalid status) verifies that neither write occurs.

### Overall finding

**No blocking findings.** Both findings are non-blocking. Step 7 is ready to commit. **Gate 3 must be cleared before Phase 4 begins. Step 7 must not be pushed until Gate 3 is cleared per user instruction.**

---

## 7. Tester Outcome

**Tester used:** Yes — AI Tester (Claude, Cowork mode), independent of Builder.

**Tester review date:** 2026-05-12

**Rationale:** Step 7 is High-risk (status change atomicity, audit log integrity). IMPLEMENTATION_WORKFLOW.md requires a separate Tester for High-risk steps.

### Tester assessment

**Test coverage assessment**

1. **Atomicity tests (S7-10, S7-13)** — `test_both_proposal_and_history_updated_atomically` verifies the positive case: after a successful POST, proposal.status is updated AND StatusHistory exists. `test_invalid_status_does_not_update_proposal` and `test_invalid_status_does_not_create_history_row` verify the negative case: form validation failure prevents both writes. This is the correct test approach for `transaction.atomic()` — the positive case confirms both writes succeed; form rejection prevents the transaction from beginning.

2. **Sensitive data tests (S7-14)** — Four tests: three check that StatusHistory model fields don't include `body`, `submitter_name`, or `submitter_contact`. The fourth (`test_status_history_row_does_not_contain_proposal_body`) confirms the stored `StatusHistory` object has no such attributes. This covers both model-level and instance-level sensitive data non-disclosure.

3. **Authorization boundary tests** — All three views (list, detail, status_change) are tested for unauthenticated (redirect) and non-staff (403) access. This matches the Step 5 approach for `@admin_required` / `AdminRequiredMixin`.

**Missing test perspectives considered:**

- **True DB rollback on partial failure:** Testing that a DB error mid-transaction causes rollback (e.g., mock `StatusHistory.objects.create` to raise `IntegrityError`) is not included. This is acceptable — `transaction.atomic()` is a Django guarantee, and testing Django internals is not required for application-level TDD.
- **Second status change (history accumulates):** Only one status change per test. Multiple changes creating multiple history rows are not tested. Acceptable — the basic design does not specify a limit, and the Gate 3 manual test covers multiple changes.
- **Pagination with >20 proposals:** Not tested in automated tests. Covered by Gate 3 manual verification (S7-16).

**Tester verdict:** All High-risk acceptance criteria (atomicity, sensitive data, authorization) are covered by TDD tests. No additional tests required. Implementation is ready for commit.

---

## 8. Human Verification Items

| ID | Item | Classification | Status |
|---|---|---|---|
| HV-S7-1 | Manual browser: view proposal list — verify ordered by -created_at, 20/page (S7-16) | Phase-blocking (Gate 3) | Pending |
| HV-S7-2 | Manual browser: view proposal detail — verify all fields, StatusHistory visible (S7-17) | Phase-blocking (Gate 3) | Pending |
| HV-S7-3 | Manual browser: change proposal status — verify DB update + StatusHistory row (S7-18) | Phase-blocking (Gate 3) | Pending |
| HV-S7-4 | Manual browser: verify unauthenticated access redirects to login with ?next= (S7-19) | Phase-blocking (Gate 3) | Pending |
| HV-S7-5 | DB-level check: verify proposal.body and submitter fields not in status_history table | Phase-blocking (Gate 3) | Pending |

**Gate note:** Human Gate 3 must be cleared before Phase 4 (Step 8) begins. Gate 3 decision recorded in `docs/implementation/gate-03-functional.md`.

---

## 9. Assumptions and Remaining Risks

| ID | Type | Description |
|---|---|---|
| SD-01 | Assumption | `AdminStatusChangeView` POST-only via View method dispatch — HTTP 405 for staff GET |
| SD-02 | Assumption | `transaction.atomic()` per basic design Section 9.1; positive atomicity tested |
| SD-03 | Assumption | Invalid status → redirect to detail with `?error=invalid_status` |
| SD-04 | Assumption | All admin CBVs use `AdminRequiredMixin` |
| SD-05 | Assumption | TDD Red→Green confirmed in Docker (19/29 red, 29/29 green) |
| SD-06 | Assumption | `_stub_list` removed; Step 5 decorator tests still pass (real view has equivalent auth) |
| R-APPEND | Risk | No automated test for `.update()`/`.delete()` on StatusHistory (Section 9.3); deferred to Step 9 |
| BD-02 | Risk | ip_address in AdminLoginLog — release-blocking for trial start |
| R-LINT | Risk | Lint not run; deferred to Step 9 |

---

## 10. ADR Compliance Notes

| ADR | Compliance |
|---|---|
| ADR-001 | N/A for Step 7 (auth mechanism unchanged) |
| ADR-002 | All admin views use `AdminRequiredMixin`; unauthenticated → redirect; non-staff → 403 ✓ |
| ADR-003 | Django CBVs, Paginator, ModelForm; no new dependencies ✓ |
| ADR-004 | N/A for Step 7 |
| ADR-005 | Status change in `transaction.atomic()`; `StatusHistory` stores only status fields and FK refs; no body/submitter fields; append-only in application code ✓ |
| ADR-006 | N/A for Step 7 |

---

## 11. Commit Hash

**Commit:** Pending

---

## 12. Push Status

**Status:** Pending commit. **Do not push until Gate 3 is cleared.** Gate 3 is phase-blocking — Phase 4 (Step 8) must not begin until Gate 3 human verification is complete.

---

*This implementation record is produced by the AI Builder. It is traceability evidence, not final acceptance, residual risk acceptance, or release approval.*
