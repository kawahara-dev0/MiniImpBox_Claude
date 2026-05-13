# Human Gate 3: Functional Acceptance

## Metadata

| Field | Value |
|---|---|
| Gate | Human Gate 3 — Phase 3 functional acceptance |
| Roadmap reference | docs/design/roadmap-v1.md — Human Gate 3 |
| Date | 2026-05-12 |
| Verifier | System Owner (human) — Kawahara |
| Covers steps | Step 6 (public proposal submission), Step 7 (admin proposal views and status change) |
| Decision | **Cleared** |

---

## Verification Results

| Item | Description | Result |
|---|---|---|
| GV3-1 | Browser: proposal list ordered by -created_at, 20 proposals per page (S7-16) | Pass |
| GV3-2 | Browser: proposal detail shows all fields and StatusHistory (S7-17) | Pass |
| GV3-3 | Browser: status change updates DB and creates StatusHistory row (S7-18) | Pass |
| GV3-4 | Browser: unauthenticated access to admin views redirects to login with ?next= (S7-19) | Pass |
| GV3-5 | DB: proposals_statushistory table has no body/submitter_name/submitter_contact columns | Pass |

---

## Decision

**Gate 3 is cleared.**

All 5 verification items passed. Phase 4 (Step 8: Backup script) may now begin. The Step 7 commits (`2eaae3e`, `a3e3af4`) may now be pushed.

---

## Pending Items (non-blocking for Gate 3)

| ID | Item | Status |
|---|---|---|
| BD-02 | ip_address logging in AdminLoginLog — privacy review pending | Release-blocking (Gate 4) |
| R-APPEND | No automated test for .update()/.delete() on StatusHistory — deferred to Step 9 | Non-blocking |
| R-LINT | Lint not run — deferred to Step 9 | Non-blocking |

---

*Gate cleared by System Owner (human). AI does not clear human gates.*
