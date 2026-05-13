# Implementation Record — Step 6: Public Proposal Submission

## Metadata

| Field | Value |
|---|---|
| Roadmap step | Phase 3, Step 6 — Public proposal submission |
| Implementation request | docs/implementation/implementation-request-v1.md |
| Roadmap | docs/design/roadmap-v1.md |
| Date | 2026-05-12 |
| Builder | AI Builder (Claude, Cowork mode) |
| Risk classification | **Medium** — public-facing form |
| TDD required | No mandatory TDD (Medium risk); tests written before implementation in practice |
| Status | Pending Implementation Reviewer sign-off |

---

## 1. Scope

Step 6 implements the public proposal submission form: `ProposalForm`, `ProposalSubmitView`, `ProposalSubmitCompleteView`, URLs, and templates.

**In scope (per roadmap-v1.md Step 6):**

- `proposals/forms.py`: `ProposalForm` — title, body, submitter_name, submitter_contact with all validation rules
- `proposals/views.py`: `ProposalSubmitView` (GET + POST), `ProposalSubmitCompleteView` (GET)
- `proposals/urls.py`: replaced Step 1 placeholder — `proposals:submit` and `proposals:submit_complete`
- `proposals/templates/proposals/submit.html`: submission form (English UI)
- `proposals/templates/proposals/submit_complete.html`: success page (English UI)
- `proposals/tests/test_forms.py`: 12 form tests
- `proposals/tests/test_views_public.py`: 15 view tests
- `docs/tests/miniimpbox_v1_test_cases.csv`: rows S6-1 through S6-11 added

**Out of scope (deferred to later steps):**

- Admin proposal list/detail/status views (Step 7)
- `StatusChangeForm` (Step 7)

---

## 2. Changed Files

| File | Action | Rationale |
|---|---|---|
| `proposals/forms.py` | Created | `ProposalForm` per basic design Section 8.1 |
| `proposals/views.py` | Created | `ProposalSubmitView`, `ProposalSubmitCompleteView` per basic design Section 5.1 |
| `proposals/urls.py` | Updated | Replaced Step 1 placeholder — `proposals:submit` and `proposals:submit_complete` per basic design Section 4.2 |
| `proposals/templates/proposals/submit.html` | Created | Submission form (English UI) per basic design Section 8 |
| `proposals/templates/proposals/submit_complete.html` | Created | Success page (English UI) |
| `proposals/tests/test_forms.py` | Created | 12 tests for ProposalForm validation |
| `proposals/tests/test_views_public.py` | Created | 15 tests for public views |
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated | Rows S6-1 through S6-11 added |

---

## 3. Implementation Notes and Assumptions

**SD-01 (Assumption): UI language is English**

All template text (labels, buttons, messages) is in English per user instruction. The basic design specified Japanese locale (`LANGUAGE_CODE = 'ja'`) for the admin-facing UI but the user explicitly requested English UI for Phase 3.

**SD-02 (Assumption): `ProposalForm.clean_submitter_contact()` uses `EmailValidator`**

Matches basic design Section 8.1 exactly. Non-empty `submitter_contact` is validated; empty value is accepted (optional field). Invalid format raises `ValidationError`.

**SD-03 (Assumption): `proposals/admin_urls.py` unchanged in Step 6**

The `_stub_list` stub (with `@admin_required`) from Step 5 remains unchanged. Real admin views are added in Step 7.

**SD-04 (Assumption): Tests written before copying implementation to container**

Although Step 6 is Medium-risk (TDD not mandatory), tests were written before the implementation files were copied to the container, achieving a practical Red→Green sequence. All 27 tests passed on first Green run.

---

## 4. Checks Run

| Check | Result | Notes |
|---|---|---|
| Step 6 tests — 27/27 pass | Pass | `27 passed in 0.77s` |
| Full test suite (90 tests) — regression check | Pass | `90 passed in 20.96s` — no regressions |
| Static review of `forms.py` against basic design Section 8.1 | Pass | `ProposalForm` matches design exactly |
| Static review of `views.py` against basic design Section 5.1 | Pass | GET/POST behavior correct; no auth check (public views) |
| Static review of `urls.py` against basic design Section 4.2 | Pass | `proposals:submit`, `proposals:submit_complete` correct |
| CSRF token in submit.html | Pass | `{% csrf_token %}` present |
| Lint (flake8/ruff) | Not run | Not installed in Docker image; deferred to Step 9 |
| CI | Not configured | Not configured for this project |

---

## 5. Test Case CSV Status

| File | Status |
|---|---|
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated — rows S6-1 through S6-11 added |

**S6-1 through S6-9** (Automated): All Pass — 27 tests passed in Docker. Version/Commit: Working tree (updated to commit hash post-commit).
**S6-10 through S6-11** (Human, Phase-blocking Gate 3): Pending — require browser-level verification.

**Coverage CSV:** Not created in Step 6. High-risk module coverage measured in Step 9.

---

## 6. Implementation Reviewer Outcome

**Reviewer:** AI Implementation Reviewer (Claude, Cowork mode) — independent of Builder

**Review date:** 2026-05-12

### Scope reviewed

- `proposals/forms.py`, `proposals/views.py`, `proposals/urls.py`
- `proposals/templates/proposals/submit.html`, `submit_complete.html`
- `proposals/tests/test_forms.py`, `proposals/tests/test_views_public.py`
- `docs/tests/miniimpbox_v1_test_cases.csv` rows S6-1 through S6-11
- Implementation record Sections 1–5
- Compliance against: basic design Sections 5.1, 8.1, 4.2, SECURITY_POLICY.md

### Findings

**Finding R1 — Non-blocking — No `@login_required` on public views (correct)**

`ProposalSubmitView` and `ProposalSubmitCompleteView` have no authentication checks. This is correct per the design ("No authentication check" for public views, basic design Section 5.1). Non-blocking.

**Finding R2 — Non-blocking — `submit_complete.html` accessible without prior submission**

`ProposalSubmitCompleteView` can be accessed directly without submitting a form (no POST-redirect-GET enforcement). The design does not require one-time-only access control for this view. Acceptable for v1 trial.

Classification: Non-blocking.

### Behavior compliance review

| Acceptance criterion | Implementation | Match |
|---|---|---|
| GET / renders proposal form | `ProposalSubmitView.get()` renders `submit.html` | ✓ |
| Valid POST: proposal saved with status=new | `form.save()` → default status='new' | ✓ |
| Valid POST: redirect to /submit/complete/ | `redirect('proposals:submit_complete')` | ✓ |
| Invalid submitter_contact: form error, no submission | `clean_submitter_contact()` raises `ValidationError` | ✓ |
| body > 2000 chars: form error, no submission | `max_length=2000` on body CharField | ✓ |
| title > 100 chars: form error, no submission | Django ModelForm max_length from model | ✓ |
| Empty title or body: form error, no submission | `required=True` (default) | ✓ |

### Security review

- `{% csrf_token %}` in submit.html ✓
- No authentication required (public view — correct per design) ✓
- Input validated through `ProposalForm`; no raw SQL or shell execution ✓
- Form errors do not expose internal details ✓
- `submitter_contact` validated as email format if non-empty ✓

### Test adequacy review

All 7 roadmap acceptance criteria are covered. Form tests independently validate each constraint. View tests confirm end-to-end behavior. No missing test perspectives identified.

### Overall finding

**No blocking findings.** Step 6 is ready to commit.

---

## 7. Tester Outcome

**Tester used:** No — Step 6 is Medium-risk. Per IMPLEMENTATION_WORKFLOW.md, a Tester is "optional by default" and "should be considered" for High-risk areas. Step 6 (public form submission) does not involve authentication, authorization, audit logs, transactions, or security-sensitive error handling. The Reviewer has confirmed test adequacy.

**Reviewer test adequacy review (in lieu of Tester):** All 7 acceptance criteria covered by automated tests. The form validation tests (`test_forms.py`) and view tests (`test_views_public.py`) together provide adequate coverage for a Medium-risk public form.

---

## 8. Human Verification Items

| ID | Item | Classification | Status |
|---|---|---|---|
| HV-S6-1 | Manual browser: submit valid proposal — verify saved with status=new (S6-10) | Phase-blocking (Gate 3) | Pending |
| HV-S6-2 | Manual browser: submit invalid contact email — verify form error, no proposal saved (S6-11) | Phase-blocking (Gate 3) | Pending |

**Gate note:** Human Gate 3 covers Steps 6 and 7 end-to-end functional acceptance. Gate 3 must be cleared before Phase 4 begins.

---

## 9. Assumptions and Remaining Risks

| ID | Type | Description |
|---|---|---|
| SD-01 | Assumption | UI in English per user instruction |
| SD-02 | Assumption | `ProposalForm.clean_submitter_contact()` uses `EmailValidator` per basic design Section 8.1 |
| SD-03 | Assumption | `proposals/admin_urls.py` stub unchanged; real views in Step 7 |
| SD-04 | Assumption | Tests written before implementation copied to container (practical Red→Green) |
| BD-02 | Risk | ip_address in AdminLoginLog — release-blocking for trial start (unchanged from Step 5) |
| R-LINT | Risk | Lint not run; deferred to Step 9 |

---

## 10. ADR Compliance Notes

| ADR | Compliance |
|---|---|
| ADR-001 | N/A for Step 6 (no authentication) |
| ADR-002 | N/A for Step 6 (public views, no authorization required) |
| ADR-003 | Django ModelForm and CBVs; no new dependencies ✓ |
| ADR-004 | N/A for Step 6 |
| ADR-005 | N/A for Step 6 (no audit log) |
| ADR-006 | N/A for Step 6 |

---

## 11. Commit Hash

**Commit:** `b78c4a3`

---

## 12. Push Status

**Status:** Pushed to `origin/master` — commit `b78c4a3`.

---

*This implementation record is produced by the AI Builder. It is traceability evidence, not final acceptance, residual risk acceptance, or release approval.*
