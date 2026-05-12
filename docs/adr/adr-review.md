# Design Review — ADR Drafts (ADR-001 through ADR-006)

## Metadata

| Field | Value |
|---|---|
| Artifacts reviewed | ADR-001 through ADR-006 |
| Review date | 2026-05-11 |
| Reviewer | AI Design Reviewer (Claude, Cowork mode) |
| Policies applied | REVIEW_POLICY.md, AGENTS.md, AI_DEVELOPMENT_POLICY.md, SECURITY_POLICY.md |
| Requirements basis | docs/requirements/requirements-v1.md (Approved 2026-05-11) |

---

## Overall Judgment

**Acceptable with concerns — workflow must stop for human acceptance of all 6 ADRs.**

All 6 ADR drafts are well-structured, internally consistent, and correctly aligned with the approved requirements. Each ADR correctly separates decided items from items deferred to basic design. No ADR makes a decision that exceeds the human-approved scope. Cross-ADR references are consistent. One auto-fixable finding was resolved during this review pass.

The workflow must stop for human acceptance of all 6 ADRs before implementation begins.

---

## What the Designer did well

**ADR-001 (Authentication Strategy)**
- Clearly distinguishes the approved high-level decision (email + password, server-side session, HTTP-only cookie) from items deferred to basic design (session expiry, hashing algorithm, failed login behavior, logout behavior, seed procedure).
- Alternatives section correctly rejects JWT-in-localStorage on XSS grounds.
- Notes explicitly call out session expiry as a security-relevant detail that must not be left to Django defaults without review.

**ADR-002 (Authorization Model)**
- Clearly establishes the two-tier model: unauthenticated = general user access only, authenticated = admin access.
- Correctly defers the `is_staff` vs. custom field decision to basic design, and flags it as a future acceptance requirement.
- Explicitly requires centralized enforcement (shared decorator/middleware) rather than per-view checks, reducing the risk of accidentally missing an auth check.

**ADR-003 (Technology Stack)**
- Rationale is specific and traces each choice back to requirements (auth risk reduction, Docker Compose ease, SSR simplicity).
- Correctly notes that package versions must be locked in basic design rather than left as floating ranges.
- Both the chosen option (Option A: Django) and the alternative (Option B: FastAPI) are evaluated fairly.

**ADR-004 (Database Persistence and Docker Compose)**
- Clearly explains why named volumes are preferred over bind mounts for DB data (Docker recommendation), and why host bind mounts are preferred for backups (direct accessibility without Docker commands).
- Explicitly documents the destructive nature of `docker compose down --volumes` as an operational risk.
- Encryption key management is correctly flagged as requiring definition in the operational runbook before the trial begins.

**ADR-005 (Audit Log Policy)**
- Append-only constraint is stated in both the Decision section (no UPDATE/DELETE by application) and reinforced in Notes (DB-layer enforcement option).
- Sensitive data prohibition is explicit and comprehensive (body, submitter_name, submitter_contact, passwords, session tokens).
- The `ip_address` nullable decision is correctly linked to the outstanding privacy/regulatory review question (A-09, R-07).

**ADR-006 (Data Retention and Operational Deletion)**
- The 7-step operational deletion procedure is specific and actionable, not vague.
- The distinction between application-level deletion (not provided) and operational procedure (human-executed) is clearly stated and traced to HD-10 and HD-17.
- Notes correctly require the deletion procedure to be documented before the trial begins, not deferred indefinitely.

---

## Auto-fixable findings (resolved)

1. **ADR-005 Related Requirements — missing cross-reference to ADR-006.** Audit log data is subject to the retention and deletion policy in ADR-006, but ADR-006 was not referenced in ADR-005's Related Requirements section. Added: "ADR-006: Data retention and operational deletion — audit log data is subject to the same 90-day retention and backup policy." *(Fixed)*

No further auto-fixable findings remain.

---

## Human-decision findings

### HDF-01: All 6 ADRs are Proposed — workflow must stop for human acceptance

All 6 ADRs have Status: Proposed. Per the design workflow (DESIGN_WORKFLOW.md) and REVIEW_POLICY.md, ADR acceptance is a human decision. AI may not accept ADRs.

Implementation must not begin until the human reviews and accepts each ADR and records the acceptance (change Status from Proposed to Accepted, add acceptance date and approver).

### HDF-02: ADR-002 — `is_staff` vs. custom admin field decision (deferred to basic design)

ADR-002 defers the choice of admin identification attribute (`is_staff` vs. custom field) to basic design. When ADR-002 is accepted, this detail must be resolved — either resolved within the ADR before acceptance, or explicitly recorded as a basic-design decision that does not block ADR acceptance. Human must decide which approach to take.

**AI recommendation:** Accept ADR-002 with the understanding that `is_staff` vs. custom field is a basic design detail, not an architectural decision requiring a separate ADR. This is consistent with the ADR template's note that conditional items in a Proposed ADR must be resolved before Accepted status.

### HDF-03: ADR-004, ADR-005, ADR-006 — Backup encryption tool and key management not yet specified (deferred to basic design / operational procedure)

Three ADRs (ADR-004, ADR-005, ADR-006) reference backup encryption as required but defer the specific tool (GPG, `age`, `openssl enc`) and key management procedure to basic design and the operational runbook. This deferral is appropriate for Proposed ADRs. However, when these ADRs are accepted, the encryption approach must be confirmed — either by resolving it within the ADR or by explicitly recording that it is a basic design detail.

**AI recommendation:** Accept the ADRs with the encryption approach deferred to basic design, then resolve it explicitly in the basic design artifact. The encryption tool selection does not change the ADR-level decisions about backup structure or retention.

---

## Missing or excessive artifacts

- No accepted ADRs yet (all are Proposed). Correct at this stage.
- No basic design document yet. Correct — ADRs must be accepted before basic design begins.
- An operational runbook / deletion procedure document is referenced in ADR-004, ADR-006. This does not need to exist before ADR acceptance, but must be created before the trial begins.

---

## Cross-ADR Consistency Check

| Check | Result |
|---|---|
| ADR-001 (session auth) ↔ ADR-002 (login_required) | Consistent: session auth produces an authenticated user; login_required checks that session |
| ADR-001 (Django auth) ↔ ADR-003 (Django 5.x) | Consistent: both reference Django's built-in auth |
| ADR-003 (PostgreSQL 16) ↔ ADR-004 (pgdata volume, pg_dump) | Consistent |
| ADR-004 (backup storage) ↔ ADR-006 (backup policy) | Consistent: ADR-006 backup policy references ADR-004 backup storage design |
| ADR-005 (audit log tables) ↔ ADR-006 (retention covers all tables) | Consistent: ADR-006 explicitly covers status_history and admin_login_log |
| ADR-005 (ip_address nullable) ↔ requirements R-07 (IP logging privacy review) | Consistent: both flag this as subject to privacy/regulatory review |

No cross-ADR inconsistencies found.

---

## Policy Issues Revealed

None.

---

## Recommended Next Action

1. **Human reviews and accepts (or requests revision of) each ADR.** For each accepted ADR: change Status from `Proposed` to `Accepted`, add acceptance date and approver name, resolve any open items noted in HDF-02 and HDF-03.
2. After all 6 ADRs are accepted, proceed to basic design (`docs/design/basic-design-v1.md`).
3. During basic design, resolve the items deferred by ADRs: session expiry policy, password hashing algorithm, failed login behavior, admin identification attribute (`is_staff` vs. custom), backup encryption tool, Docker Compose service configuration details, and Django project structure.
4. Before the trial begins, the operational deletion procedure document must be created and reviewed.

---

## Human Verification Required

### Phase-blocking

- Human must accept all 6 ADRs (or request revisions) before basic design begins.
- ADR-002: `is_staff` vs. custom admin field must be resolved in basic design before implementation of the authorization layer.

### Non-blocking

- HDF-03 (backup encryption tool) may be resolved during basic design without blocking ADR acceptance.

### Release-blocking

- ADR-006: Operational deletion procedure document must be created before the trial begins.
- ADR-004: Backup restore must be tested at least once before relying on it.
- ADR-005, ADR-006: `ip_address` logging decision (A-09) must be confirmed under privacy/regulatory review before production.

---

## Final Note

Final completion must be determined by human review, required tests, and manual verification.

These design artifacts are ready for human review.

---

## Current Review Result

**Outcome: Acceptable with concerns — workflow must stop for human acceptance of all 6 ADRs.**

All ADRs are internally consistent and correctly aligned with approved requirements. One auto-fixable finding resolved. No policy violations. The only required action is human acceptance of each ADR.
