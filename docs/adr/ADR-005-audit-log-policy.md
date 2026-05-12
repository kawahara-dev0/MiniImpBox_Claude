# ADR-005: Audit Log Policy

## Status

Accepted

Approved by: System Owner (human) — 2026-05-11

---

## Context

Mini Improvement Box v1 requires an audit trail for specific events. The following requirements are established:

- **Status change history is required.** Every proposal status change must be recorded with proposal ID, old status, new status, the acting administrator's identifier, and a timestamp (HD-09, HD-19, FR-ADMIN-05).
- **Administrator login success and failure events must be logged** with timestamp and email. No password or session token may appear in the log (HD-19, FR-AUTH-06).
- **Administrator proposal view history is not required** for v1 (HD-19).
- **Sensitive data must not appear in any log.** Specifically prohibited from logs: proposal body, submitter_name, submitter_contact, passwords, and session information (HD-19, HD-16, NFR-04, SECURITY_POLICY.md).
- No audit log browsing UI is required for v1. Log data is accessible at the database level only (Section 10, out of scope).
- The technology stack is Django 5.x + PostgreSQL 16 (ADR-003).

The audit log design must be: sufficient for accountability and incident investigation, consistent with the data minimization principle (HD-18), and safe — it must never record sensitive personal data.

---

## Decision

### Audit Log Storage

All audit log data is stored in **dedicated tables in the PostgreSQL database**. No separate log file, external logging service, or log aggregation system is used in v1.

### Event 1: Proposal Status Change History

**Table:** `status_history`

| Column | Type | Content |
|---|---|---|
| `id` | integer / UUID | Primary key |
| `proposal_id` | FK → proposals | The proposal that was changed |
| `changed_by_id` | FK → admin_users | The administrator who made the change |
| `old_status` | varchar | Status value before the change |
| `new_status` | varchar | Status value after the change |
| `changed_at` | timestamp with timezone | Time of the change |

**Rules:**
- A row is inserted into `status_history` every time an administrator successfully changes a proposal's status.
- The record is created atomically with the status update (within the same database transaction).
- The `changed_by_id` must reference the authenticated administrator's user ID at the time of the change.
- Status history rows are never updated or deleted by the application. They are append-only.

**What is NOT recorded:** proposal body, submitter_name, or submitter_contact.

### Event 2: Administrator Login Log

**Table:** `admin_login_log`

| Column | Type | Content |
|---|---|---|
| `id` | integer / UUID | Primary key |
| `email` | varchar(254) | The email address used in the login attempt |
| `success` | boolean | True for successful login; False for failed login |
| `ip_address` | varchar | The client IP address — nullable; see Notes |
| `attempted_at` | timestamp with timezone | Time of the login attempt |

**Rules:**
- A row is inserted for every login attempt (both success and failure) by any administrator.
- The email recorded is the email submitted in the login form, regardless of whether it corresponds to an existing account.
- **No password, session token, or any credential is recorded.**
- Login log rows are never updated or deleted by the application. They are append-only.

### Events NOT logged

The following events are explicitly **not** logged in v1 (HD-19):
- Administrator proposal view history (who viewed which proposal).
- General user proposal submission (no user identity to log; proposal data is in the `proposals` table).
- Administrator logout events (may be added in basic design if considered operationally useful, but not required by HD-19).

### Sensitive Data Prohibition

The following data must **never** appear in:
- The `status_history` table
- The `admin_login_log` table
- Django application logs (`logging` module output)
- Any other log or monitoring output

Prohibited data: proposal `body`, `submitter_name`, `submitter_contact`, passwords (in any form), session tokens or session IDs, and any data derived from these fields.

### Log Access

Audit log data is accessible at the database level only (direct SQL query or Django admin, if Django admin is enabled in basic design). There is no application-level UI for browsing audit logs in v1.

---

## Alternatives Considered

**A. Application log files (structured JSON logs)**
Writing audit events to structured log files (e.g., via Python `logging` with JSON formatter) is a common alternative. However, log files require file lifecycle management (rotation, archival, access control) separate from the application database. For v1, storing audit events in the database is simpler, consistent with data retention policy, and queryable via SQL.

**B. External log aggregation service (e.g., ELK stack, CloudWatch Logs)**
Out of scope for a v1 limited internal trial. Adds infrastructure and cost overhead unjustified for the scale and scope.

**C. Django signals for audit logging**
Django signals (e.g., `post_save` on the proposal model) could trigger audit log writes. However, signals can be silently missed if the signal is not connected, and they decouple the audit write from the transaction boundary. Direct, explicit audit log writes in the service/view layer (within the same transaction) are more reliable.

**D. No audit log**
Not acceptable. HD-19 explicitly requires status change history and login event logging.

---

## Reasons

- **Database-backed audit log** is consistent with the overall data storage approach (PostgreSQL), subject to the same retention and backup policy (HD-17), and queryable via SQL.
- **Append-only rows** ensure the audit trail cannot be altered by the application. Rows must never be updated or deleted by application code.
- **Same-transaction status history write** guarantees that if a status change is committed, its history record is also committed. There is no window where a status change exists without a history record.
- **Explicit prohibition of sensitive data** in log tables is required by HD-19 and SECURITY_POLICY.md. This must be enforced in implementation and verified in review.
- **Not logging proposal body and submitter fields** implements data minimization (HD-18) in the audit log layer. The full data is available in the `proposals` table for authorized administrators; the audit log needs only the event metadata.

---

## Consequences

**Positive:**
- Audit trail is stored in the same database as application data, simplifying backup (one backup covers all data).
- Status history is directly queryable and linkable to proposals.
- No external logging infrastructure required for v1.
- Append-only rows provide tamper-resistance at the application layer.

**Negative:**
- Audit log is in the same database as application data. A compromised database exposes both application data and audit logs. In a higher-security environment, logs should be in a separate, append-only data store.
- No UI for browsing audit logs in v1. Reviewing logs requires database access, which limits operational usability.
- If the `admin_login_log` grows large over time (many failed login attempts), it may need archival or partitioning. For a limited internal trial, this is not an immediate concern.

---

## Related Requirements

- FR-ADMIN-05: Administrator can view status change history of a proposal.
- FR-AUTH-06: Administrator login success and failure events must be logged.
- HD-09: Status change history required; no comments.
- HD-16: Proposal body may contain personal data; must not appear in logs.
- HD-17: Audit log data subject to 90-day retention and backup policy.
- HD-18: Data minimization; log only what is necessary.
- HD-19: Audit log requirements — what is required, what is prohibited.
- NFR-04: Proposal body and submitter fields must not appear in application logs.
- SECURITY_POLICY.md: Sensitive data must not be logged; audit logs must be preserved.
- ADR-003: Technology stack (Django 5.x + PostgreSQL 16).
- ADR-006: Data retention and operational deletion — audit log data is subject to the same 90-day retention and backup policy as proposal data.

---

## Notes

- The `ip_address` field in `admin_login_log` is optional (nullable). Whether to populate it depends on the outcome of the privacy/regulatory review (HD-18, R-07 in requirements). If applicable regulations restrict IP address logging, this field should be omitted or left null. The decision must be made before the trial begins.
- Logout event logging is not required by HD-19. If it is added in basic design for operational visibility, it must also comply with the sensitive data prohibition (no session token in the logout log).
- The append-only constraint for audit log rows must be enforced at the application layer (no `UPDATE` or `DELETE` statements on these tables in application code). It may also be enforced at the database layer with a `RULE` or `TRIGGER` in a later version if tamper-resistance is a higher priority.
- Re-evaluate this policy if v2 expands to a production environment where log separation, log integrity, and log access control become more critical.
