# ADR-006: Data Retention and Operational Deletion Procedure

## Status

Accepted

Approved by: System Owner (human) — 2026-05-11

---

## Context

Mini Improvement Box v1 handles data that may contain personal or confidential information:

- Proposal body: may contain personal or confidential information (HD-16).
- Submitter name and submitter contact: optional personal data (HD-16).
- Administrator email address: personal identifier used for authentication and audit (HD-05).
- Status change history and login logs: audit data linked to administrator identifiers.

The following retention requirements are established:

- **Proposal data is retained for 90 days from the end of the trial** (HD-17).
- **Daily backups during the trial period; 14 backup generations retained** (HD-17).
- **Backup encryption is required** (HD-17).
- **Post-retention deletion is an operational procedure, not an application feature** (HD-10, HD-17). The application does not provide a deletion API or UI.
- **Rate limiting / anti-spam** is out of scope; proposal volume is bounded by the limited internal trial context (HD-12, A-07).
- v1 is a limited internal trial. No public release or production operation. Privacy/regulatory review required before production (HD-18).
- The technology stack is Django 5.x + PostgreSQL 16 + Docker Compose (ADR-003, ADR-004).

A clear, documented data lifecycle policy is required to: limit personal data exposure, comply with the data minimization principle (HD-18), and ensure the trial can be cleanly concluded without residual data.

---

## Decision

### Retention Period

**All proposal data, audit logs, and administrator account data are retained for 90 days from the trial end date.**

The trial end date must be explicitly defined and recorded before the trial begins. The retention period ends 90 days after that date.

### Backup Policy

- **Frequency:** Daily, during the active trial period.
- **Retention:** 14 most recent daily backup files are retained. The backup script must delete files beyond the 14-generation limit as part of each backup run.
- **Encryption:** Every backup file must be encrypted before or during write to the backup destination. The specific encryption tool and key management procedure are defined in the operational procedure documentation (basic design / operational runbook).
- **Location:** Host-mounted directory outside ephemeral container storage (ADR-004).
- **Backup file coverage:** Full database dump (`pg_dump`), covering all tables: `proposals`, `status_history`, `admin_login_log`, and the administrator user table.

### Post-Retention Deletion

Post-retention deletion is **not** an application feature. No deletion API or UI is provided in v1. Deletion is executed as an **approved operational procedure** by the system owner after the retention period ends.

The operational deletion procedure must include at minimum:
1. Confirm the retention period has ended (90 days from trial end date).
2. Stop the application service to prevent new writes.
3. Delete all proposal and audit data from the database (SQL `TRUNCATE` or `DROP TABLE` + `CREATE TABLE`, or targeted `DELETE` statements).
4. Delete all administrator accounts (or deactivate them if the system will be reused).
5. Delete all backup files from the backup directory.
6. Remove the backup encryption key (or archive it securely if the key is reused for a future trial).
7. Record the deletion event (date, executor, confirmation that data has been removed).

The deletion procedure must be documented before the trial begins and reviewed by the system owner.

### Application-Level Deletion

The application does not provide:
- Proposal deletion by general users or administrators (FR-ADMIN-09, FR-PROP-06, HD-10).
- Automated data expiry or cleanup within the application.
- A data export or data erasure API.

### Backup Encryption Key Management

The encryption key used for backup files:
- Must not be stored in the repository.
- Must not be stored in the backup directory alongside the backup files.
- Must be stored in a secure location accessible only to the system owner.
- The key storage location and recovery procedure must be documented in the operational runbook.

---

## Alternatives Considered

**A. Application-level automated deletion (scheduled job)**
A Django management command or Celery task could automatically delete records older than the retention period. This is more robust than relying on a manual procedure but: (a) it requires a scheduler or task queue (additional infrastructure); (b) automated deletion of personal data is an irreversible operation that benefits from human oversight; (c) it is out of scope for v1's limited internal trial. Recommended for evaluation in v2 if the system transitions to production.

**B. No defined retention period**
Without a defined retention period, personal data would be retained indefinitely, which conflicts with the data minimization principle (HD-18) and may be inconsistent with applicable regulations. This is not acceptable.

**C. Shorter retention period (e.g., 30 days)**
A shorter retention period reduces data exposure but may not provide enough time for post-trial analysis. 90 days was specified in HD-17.

**D. No backup encryption**
Backup files contain personal data (proposal body, submitter information). Unencrypted backup files would expose personal data to anyone who can read the backup directory. Encryption is required by HD-17 and consistent with SECURITY_POLICY.md.

---

## Reasons

- **Human-executed deletion** is appropriate for a limited internal trial. It ensures a human explicitly confirms that the retention period has ended and that deletion is intentional. Irreversible data deletion should have a human approval step.
- **Defined retention period** (90 days post-trial) bounds the personal data exposure window and provides a clear deadline for post-trial cleanup.
- **Backup encryption** is required because backup files may contain personal data and must be protected even if the backup directory is accessed without authorization.
- **14-generation daily backup** provides approximately two weeks of recovery window, sufficient for an internal trial.
- **Backup script-managed retention** (deleting old files as part of each backup run) ensures the backup directory does not grow unboundedly and that retention is enforced automatically during the trial period.

---

## Consequences

**Positive:**
- Personal data is retained for a defined, bounded period.
- Backup files are encrypted, limiting exposure.
- Post-retention deletion is explicit and human-controlled.
- Clear documented procedure supports accountability.

**Negative:**
- Post-retention deletion relies on human execution. If the procedure is not followed, retention cannot be enforced. Mitigation: document the procedure, set a calendar reminder for the deletion date, and record execution.
- The backup encryption key must be managed securely. Loss of the key makes encrypted backups unrecoverable.
- No automated data lifecycle enforcement in v1. This is a known limitation accepted for the scope of a limited internal trial.

---

## Related Requirements

- HD-10: No application-level deletion feature.
- HD-16: Personal data collected (submitter_name, submitter_contact, proposal body).
- HD-17: 90-day retention, daily backups, 14 generations, backup encryption — all decided by human.
- HD-18: Data minimization, access restriction; privacy/regulatory review before production.
- FR-ADMIN-09: Proposal deletion not available via application screens or APIs.
- FR-PROP-06: General users cannot delete proposals.
- SECURITY_POLICY.md: Sensitive data must be protected; secrets must not be committed.
- ADR-004: Database persistence and Docker Compose environment (backup storage, encryption location).
- ADR-005: Audit log policy (audit log data also subject to this retention policy).

---

## Notes

- The trial end date must be recorded in writing before the trial begins. The retention expiry date (trial end + 90 days) must be communicated to the system owner.
- A calendar reminder or operational checklist item should be created at trial start for the deletion date.
- The operational deletion procedure document must be written and reviewed before the trial begins. It must not be left as an undefined action for after the trial.
- If the trial is extended, the retention period and the deletion date must be explicitly re-evaluated and re-recorded.
- Before production deployment (if any), automated data lifecycle enforcement (e.g., scheduled deletion job) should replace the manual procedure, and this ADR should be revisited.
- Privacy/regulatory review (HD-18) may impose additional requirements (e.g., right to erasure, data processing records, consent mechanism) before production. This ADR may need revision at that time.
