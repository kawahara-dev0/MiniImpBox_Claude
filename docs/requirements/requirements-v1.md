# Requirements — Mini Improvement Box v1

## Metadata

| Field | Value |
|---|---|
| Status | Approved |
| Version | v1 |
| Created | 2026-05-11 |
| Updated | 2026-05-11 |
| Author | AI Designer (Claude, Cowork mode) |
| Approver | System Owner (human) — approved 2026-05-11 |
| Policies checked | AGENTS.md, AI_DEVELOPMENT_POLICY.md, AI_RULES.md, REVIEW_POLICY.md, SECURITY_POLICY.md, DESIGN_WORKFLOW.md |
| ADRs checked | None — docs/adr/ contains no accepted ADRs at time of draft |

---

## 1. Purpose

Mini Improvement Box is a small-scale web application that enables unauthenticated general users to post improvement proposals, and authenticated administrators to review and manage those proposals.

The goal of v1 is to establish a minimal, operable system covering the core proposal lifecycle: submission by general users (no login required), browsing and status management by administrators, with appropriate access control, data persistence, and audit trail.

v1 is scoped as a limited internal trial and is not intended for public release or production operation.

---

## 2. Stakeholders

| Role | Description |
|---|---|
| General User | Anyone who submits an improvement proposal (no login required) |
| Administrator User | A pre-provisioned privileged user who manages proposals |
| System Owner | Human responsible for the system; holds requirement approval, risk acceptance, and release authority |

---

## 3. User Roles

### Role Model

v1 defines two distinct user types. A single account cannot hold both roles simultaneously — the dual-role design is out of scope for v1. (Decided: HD-02)

| Role | Authentication | Access |
|---|---|---|
| General User | Not required (unauthenticated) | Proposal submission form only |
| Administrator User | Required (email + password) | All admin screens — proposal list, detail, status change |

### Administrator Provisioning

Administrator accounts are created via a seed script or management script executed at deployment time. There is no UI-based self-registration, admin registration UI, or admin promotion for v1. (Decided: HD-01, HD-04, HD-03-AI)

The seed or management script must:
- Create at least one admin account with a unique email address and a securely hashed password.
- Not commit credentials to the repository.
- Accept credentials via environment variables or a secure input mechanism.

Detailed seed/admin creation procedure will be defined in basic design. (HD-03-AI)

---

## 4. Functional Requirements

### 4.1 Authentication

> **Context**: General users require no authentication. Administrators authenticate with email and password using server-side session. No UI-based self-registration, admin registration UI, or password reset UI is provided in v1. Detailed session design, password hashing algorithm, failed login behavior, logout behavior, and seed/admin creation procedure will be defined in basic design. (Decided: HD-02, HD-03, HD-03-AI, HD-04)

| ID | Requirement | Decided / Status |
|---|---|---|
| FR-AUTH-01 | General users do not need to authenticate to submit a proposal. | Decided (HD-02) |
| FR-AUTH-02 | Administrator users must authenticate with their email address and password before accessing any admin screen or operation. | Decided (HD-03, HD-05, HD-03-AI) |
| FR-AUTH-03 | Administrators authenticate via server-side session (HTTP-only cookie). Specific session expiry and renewal behavior to be defined in basic design. | Decided (HD-03-AI) |
| FR-AUTH-04 | Administrator users must be able to log out. Logout behavior (session invalidation) to be defined in basic design. | Decided (HD-03-AI) |
| FR-AUTH-05 | Failed login attempts must not expose whether the email address exists. | Decided (SECURITY_POLICY.md baseline) |
| FR-AUTH-06 | Administrator login success and login failure events must be logged with timestamp and email (no password, no session token). | Decided (HD-19) |
| FR-AUTH-07 | There is no general user account registration UI, admin registration UI, or password reset UI in v1. | Decided (HD-02, HD-04, HD-03-AI) |

### 4.2 Proposal Submission (General User)

> **Context**: General users are unauthenticated. Proposals are not linked to a user account. Submitter identity is collected as optional free-text fields. (Decided: HD-02, HD-06, HD-16)

| ID | Requirement | Decided / Status |
|---|---|---|
| FR-PROP-01 | Any user (unauthenticated) must be able to submit an improvement proposal via a web form. | Decided (HD-02) |
| FR-PROP-02 | A proposal must include the following fields: `title` (required), `body` (required), `submitter_name` (optional), `submitter_contact` (optional). | Decided (HD-06) |
| FR-PROP-03 | Field constraints: `title` 1–100 characters; `body` 1–2000 characters; `submitter_name` 0–100 characters; `submitter_contact` 0–254 characters, and must conform to email format when provided. A submission with an invalid `submitter_contact` format must be rejected with a validation error; the field must not be silently truncated or ignored. | Decided (HD-06) |
| FR-PROP-04 | On successful submission, the proposal status is automatically set to `new`. | Decided (HD-08) |
| FR-PROP-05 | After successful submission, the user receives a confirmation (e.g., success message on the same page). | Proposed |
| FR-PROP-06 | General users cannot edit or delete a proposal after submission. | Decided (HD-10) |
| FR-PROP-07 | General users do not have access to a proposal list, proposal details, status history, or any admin screen. | Decided (HD-07) |

**[Assumption — AI]** General users receive only a one-time confirmation message after submission. There is no proposal tracking page for submitters in v1.

### 4.3 Proposal Management (Administrator)

> **Context**: Administrators can browse all proposals with pagination, view individual proposal details including status history, and change proposal status. No filter/sort, no comment, no deletion in v1. (Decided: HD-07, HD-08, HD-09, HD-10, HD-11)

| ID | Requirement | Decided / Status |
|---|---|---|
| FR-ADMIN-01 | An authenticated administrator must be able to browse all submitted proposals. | Decided (HD-07) |
| FR-ADMIN-02 | The proposal list must support pagination or a maximum result limit to avoid unbounded rendering. Default order is most recent first (by `created_at` descending or `updated_at` descending). | Decided (HD-11, HD-12) |
| FR-ADMIN-03 | Filter and sort controls are out of scope for v1. | Decided (HD-11) |
| FR-ADMIN-04 | An authenticated administrator must be able to view the full details of a single proposal, including all fields and the current status. | Decided (HD-07) |
| FR-ADMIN-05 | An authenticated administrator must be able to view the status change history of a proposal (who changed it, to what value, at what time). | Decided (HD-09, HD-19) |
| FR-ADMIN-06 | An authenticated administrator must be able to change the status of a proposal to any valid status value. | Decided (HD-08) |
| FR-ADMIN-07 | Invalid status values must be rejected. | Decided (HD-08) |
| FR-ADMIN-08 | There is no comment, reply, or discussion feature for administrators on proposals in v1. | Decided (HD-09) |
| FR-ADMIN-09 | Proposal deletion is not available via application screens or APIs in v1. | Decided (HD-10) |

**Proposal Status Values** (Decided: HD-08)

| Status | Meaning |
|---|---|
| `new` | Initial status; set automatically on submission |
| `reviewing` | Administrator has started reviewing the proposal |
| `planned` | The proposal has been accepted and is planned for implementation |
| `done` | The proposed improvement has been implemented |
| `declined` | The proposal has been declined |

Allowed transitions: any valid status to any other valid status (no restricted state machine for v1). Invalid (unknown) status values must be rejected.

### 4.4 Access Control

| ID | Requirement | Decided / Status |
|---|---|---|
| FR-AC-01 | Unauthenticated users can only access the proposal submission form. All other pages must redirect or return an appropriate error. | Decided (HD-02, HD-07) |
| FR-AC-02 | Administrator screens (proposal list, detail, status change) must not be accessible to unauthenticated users. | Decided (HD-07) |
| FR-AC-03 | There is no inter-user proposal visibility for general users, as proposals are not associated with user accounts in v1. | Decided (HD-02, HD-07) |
| FR-AC-04 | An authenticated administrator must not be able to access another administrator's credentials or session data. | Decided (SECURITY_POLICY.md baseline) |

---

## 5. Non-Functional Requirements

| ID | Requirement | Decided / Status |
|---|---|---|
| NFR-01 | The application must be a web-based application accessible from a standard modern browser without requiring additional plugins. | Proposed |
| NFR-02 | v1 is a limited internal trial. Large-scale, high-load, or public-facing operation is out of scope. | Decided (HD-12) |
| NFR-03 | The application must not expose sensitive user data (proposal contents, submitter information, admin credentials) to unauthorized users. | Decided (SECURITY_POLICY.md baseline) |
| NFR-04 | Proposal body and submitter fields must be treated as potentially containing personal or confidential information. They must not appear in application logs. | Decided (HD-16, HD-19) |
| NFR-05 | No formal availability or response time SLA is defined for v1. The application should be practically responsive for a small internal trial. | Decided (HD-14) |
| NFR-06 | The application must run in Docker Compose for development and trial verification. | Decided (HD-15, HD-15-AI) |
| NFR-07 | Database data files and backup files must not be stored only in ephemeral container storage. A named Docker volume or host-mounted path must be used for the database, and backups must be written to a durable location. | Decided (HD-15, HD-15-AI) |
| NFR-08 | The technology stack is Django + PostgreSQL + Docker Compose. Detailed package versions, directory structure, schema, authorization implementation, and logging design will be defined in basic design and ADRs. | Decided (HD-13-AI) |

---

## 6. Technology Stack

> **Decided (Human approved 2026-05-11 — HD-13-AI).** The following technology stack is approved for v1. Detailed package versions, directory structure, schema, authorization implementation, and logging design will be defined in the basic design artifact and ADRs. This section is included for early alignment; the detailed design belongs to the basic design phase.

### Approved Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python 3.12+ | — |
| Web Framework | Django 5.x | Built-in session auth, ORM, migrations |
| ORM + Migrations | Django ORM + built-in migrations | — |
| Templating | Django templates | Server-side rendering; no separate frontend framework |
| Authentication | Django's built-in session auth (email + password, HTTP-only cookie) | Specific session expiry / hashing algorithm in basic design |
| Database | PostgreSQL 16 | Named Docker volume for durability |
| Test framework | pytest + pytest-django | — |
| Containerization | Docker Compose | Development and trial verification only |
| DB persistence | Docker named volume (`pgdata`) | Must survive container recreation |
| Backup storage | Host-mounted directory or named backup volume | Encrypted; 14 daily generations |

**Rationale:** Django provides battle-tested built-in session-based email/password authentication, ORM, and migration tooling, minimizing implementation risk for the authentication module. Server-side rendering with Django templates eliminates frontend build complexity for v1. PostgreSQL with named Docker volumes provides durable, production-representative persistence.

### Docker Compose Environment Design

> **Decided (Human approved 2026-05-11 — HD-15-AI).** This covers development and trial verification only. It is not production release or production operation approval. Backup, restore, encryption, retention, and deletion procedure details will be defined in basic design and operational procedure documentation.

The Docker Compose configuration for v1 must meet the following requirements:

- `app` service: Django application container (stateless).
- `db` service: PostgreSQL container. Database data must use a named Docker volume or host-mounted path that survives container recreation. Data must not remain only in ephemeral container storage.
- Backup: A mechanism to write encrypted daily backup files (`pg_dump` or equivalent) to a durable host-mounted or named-volume location. At least 14 daily backup generations must be retained. Backup encryption is required (HD-17). Details in basic design / operational procedure.
- Secrets: All credentials (DB password, Django secret key, admin seed credentials) passed via `.env` file or equivalent mechanism; never committed to the repository.

---

## 7. Data Model Overview

> **[AI-generated preliminary outline — for early alignment only; not a pending approval item.]** This data model outline is included to support alignment on data scope and log-safety requirements. It does not require separate human approval at this stage. Detailed column types, constraints, index design, and migration strategy will be defined and reviewed in the basic design artifact.

### `proposals` table

| Column | Type | Constraints |
|---|---|---|
| `id` | integer / UUID | primary key |
| `title` | varchar(100) | not null |
| `body` | text (max 2000 chars) | not null |
| `submitter_name` | varchar(100) | nullable |
| `submitter_contact` | varchar(254) | nullable; email format enforced at application layer |
| `status` | varchar / enum | not null; default `new`; one of: new / reviewing / planned / done / declined |
| `created_at` | timestamp | not null |
| `updated_at` | timestamp | not null |

### `status_history` table

| Column | Type | Constraints |
|---|---|---|
| `id` | integer / UUID | primary key |
| `proposal_id` | FK → proposals | not null |
| `changed_by` | FK → admin users | not null |
| `old_status` | varchar | not null |
| `new_status` | varchar | not null |
| `changed_at` | timestamp | not null |

### `admin_users` table (or Django built-in `auth_user`)

| Column | Type | Constraints |
|---|---|---|
| `id` | integer / UUID | primary key |
| `email` | varchar(254) | unique; not null |
| `password` | varchar | hashed; not null |
| `is_active` | boolean | not null |
| `created_at` | timestamp | not null |

### `admin_login_log` table

| Column | Type | Constraints |
|---|---|---|
| `id` | integer / UUID | primary key |
| `email` | varchar(254) | not null (attempted email) |
| `success` | boolean | not null |
| `ip_address` | varchar | nullable — see A-09 |
| `attempted_at` | timestamp | not null |

> **Log safety rule:** Proposal body, submitter_name, and submitter_contact must never appear in any log table or application log output. (Decided: HD-19, HD-16)

---

## 8. Data, Privacy, and Retention

| Item | Decision |
|---|---|
| Personal data collected | Optional `submitter_name` and optional `submitter_contact` (email format). Proposal `body` may contain personal or confidential information and must be treated accordingly. (Decided: HD-16) |
| Admin identifier | Email address — unique, used for authentication and audit identification. (Decided: HD-05) |
| Data minimization | Only collect what is listed above. No tracking, analytics, or additional profiling data in v1. (Decided: HD-18) |
| Log safety | Proposal body, submitter_name, submitter_contact, passwords, and session tokens must not appear in application logs or audit logs. (Decided: HD-19) |
| Access restriction | Admin screens and proposal data are accessible only to authenticated administrators. (Decided: HD-07) |
| Trial retention period | Proposal data is retained for 90 days from the end of the trial. (Decided: HD-17) |
| Backup policy | Daily backups during the trial period; 14 backup generations retained; backups must be encrypted. (Decided: HD-17) |
| Post-retention deletion | Deletion after retention period is an approved operational procedure, not an application feature. (Decided: HD-10, HD-17) |
| Privacy/regulatory scope | v1 is a limited internal trial, not a public release. Data minimization, access restriction, safe logging, and backup protection are implementation baselines. Privacy/regulatory review must be conducted before any production release. (Decided: HD-18) |

---

## 9. Audit and Logging

| Item | Decision |
|---|---|
| Status change history | Required. Every status change must be recorded with: proposal ID, old status, new status, acting administrator (identifier), timestamp. (Decided: HD-09, HD-19) |
| Admin login success | Required. Log: email, timestamp, outcome (success). No password, no session token. (Decided: HD-19) |
| Admin login failure | Required. Log: attempted email, timestamp, outcome (failure). (Decided: HD-19) |
| Admin proposal view history | Not required for v1. (Decided: HD-19) |
| Sensitive data in logs | Prohibited: proposal body, submitter_name, submitter_contact, passwords, session information. (Decided: HD-19) |

---

## 10. Out of Scope for v1

The following items are explicitly out of scope. They must not be implemented unless a human explicitly approves their inclusion.

- Email notification to submitters when their proposal status changes
- Voting or upvoting of proposals
- Public-facing proposal board
- Attachment or file upload support
- Proposal categories, tags, or structured classification
- Admin role management UI (promoting/demoting users)
- Admin registration UI or admin invite flow
- Password reset UI
- Public self-registration for any role
- External API access for integrations
- Multi-language (i18n) support
- Analytics or reporting dashboard
- Audit log browsing UI for administrators
- Proposal editing or deletion by submitters or administrators (application feature)
- Comment, reply, or discussion feature on proposals
- Filter or sort controls on the proposal list
- Rate limiting / anti-spam on proposal submission — **[Assumption — AI]** omitted for v1 internal trial; must be re-evaluated before any public-facing deployment

---

## 11. Assumptions

| ID | Assumption | Source |
|---|---|---|
| A-01 | v1 targets a small, closed internal trial user base. Public-facing operation is not in scope. | Decided (HD-12, HD-18) |
| A-02 | General users are unauthenticated and anonymous; proposals are not linked to user accounts. | Decided (HD-02) |
| A-03 | General users receive a one-time confirmation message after submission. There is no proposal tracking page for submitters in v1. | AI Assumption |
| A-04 | Admin accounts are created via seed/script; credentials are accepted via environment variable, never via committed files. | Decided (HD-01, HD-04, HD-03-AI) |
| A-05 | Proposal body may contain personal or confidential information and must be treated with appropriate access control and log safety. | Decided (HD-16, HD-19) |
| A-06 | No email notifications are required for v1. | Out of scope (consistent with HD-04) |
| A-07 | Rate limiting on proposal submission is not required for v1 internal trial. This assumption must be re-evaluated before any public-facing use. | AI Assumption |
| A-08 | There is no multi-language requirement for v1. | Out of scope |
| A-09 | The IP address of admin login attempts may be logged as an optional operational aid, subject to applicable data handling rules. This assumption requires confirmation if a privacy/regulatory review identifies constraints. | AI Assumption — confirm under HD-18 review before production |

---

## 12. Human Decisions — Resolved Summary

All 19 original HD items and 3 AI proposals (HD-03-AI, HD-13-AI, HD-15-AI) have been resolved. No phase-blocking items remain.

| ID | Topic | Decision | Blocking? |
|---|---|---|---|
| HD-01 | Admin provisioning | Seed or management script; no UI self-registration | Resolved |
| HD-02 | Role model | Unauthenticated General User + authenticated Administrator; no dual-role | Resolved |
| HD-03 | Admin authentication method | Email + password; General user = no auth required | Resolved |
| HD-03-AI | Auth detail (session, hashing, behaviors) | **Human approved 2026-05-11.** Server-side session, HTTP-only cookie; details (session expiry, hashing algorithm, failed login/logout behavior, seed procedure) → basic design. Password reset UI / admin registration UI / public self-registration = out of scope. | Resolved |
| HD-04 | User registration policy | No UI self-registration; General user = anonymous; Admin = pre-created | Resolved |
| HD-05 | Primary user identifier | Email for admin auth and audit identification | Resolved |
| HD-06 | Proposal fields and constraints | title (1–100), body (1–2000), submitter_name (0–100, optional), submitter_contact (0–254, optional, email format) | Resolved |
| HD-07 | Proposal visibility | General/unauthenticated users cannot access admin screens, proposal list, detail, status history, or status change | Resolved |
| HD-08 | Status set and transitions | new / reviewing / planned / done / declined; initial = new; admin can change to any valid status | Resolved |
| HD-09 | Admin comments | Not in v1 scope; status change history required; no comment/reply/discussion | Resolved |
| HD-10 | Proposal deletion | No application-level deletion in v1; post-retention deletion = operational procedure | Resolved |
| HD-11 | Filter/sort | Not required; pagination or max result limit required; default order = recent first | Resolved |
| HD-12 | Expected scale | Limited internal trial; no large-scale | Resolved |
| HD-13 | Technology stack | Django + PostgreSQL + Docker Compose | Resolved |
| HD-13-AI | Stack detail | **Human approved 2026-05-11 (Option A).** Django 5.x + PostgreSQL + Docker Compose; limited internal trial; implementation details (package versions, directory structure, schema, authorization implementation, logging design) → basic design / ADR | Resolved |
| HD-14 | SLA | No formal SLA; practical for small internal trial | Resolved |
| HD-15 | Hosting and deployment | Docker Compose for dev/trial verification | Resolved |
| HD-15-AI | Environment design detail | **Human approved 2026-05-11.** Docker Compose dev/trial environment; DB data and backups not ephemeral; details (backup, restore, encryption, retention, deletion procedure) → basic design / operational procedure. Not production release/operation approval. | Resolved |
| HD-16 | Personal data collected | Optional submitter_name and submitter_contact; proposal body treated as potentially personal/confidential | Resolved |
| HD-17 | Data retention | 90 days post-trial; daily backups; 14 generations; backup encryption required; post-retention deletion = operational | Release-blocking (operational readiness) |
| HD-18 | Privacy/regulatory scope | Limited internal trial baseline; privacy/regulatory review required before production release | Release-blocking (before production) |
| HD-19 | Audit log requirements | Status change history + admin login success/failure required; no proposal view history; no sensitive data in logs | Resolved |

---

## 13. Risks

| ID | Risk | Severity | Note |
|---|---|---|---|
| R-01 | Authentication session design details (expiry, renewal, invalidation on logout) are deferred to basic design. Gaps or errors in session design could create security vulnerabilities. | High | Must be addressed explicitly in basic design and verified in access control tests. |
| R-02 | Proposal body and submitter fields may contain sensitive personal data. Accidental logging or exposure would constitute a data incident. | High | Must be verified in implementation review and access control tests. |
| R-03 | Backup encryption (HD-17) is required. If encryption implementation is omitted or weak, backups containing personal data are at risk. | High | Must be verified in pre-trial readiness check (release-blocking). |
| R-04 | Post-retention deletion is an operational procedure, not an application feature. If the procedure is not defined and executed, retention policy cannot be enforced. | Medium | Define the operational deletion procedure before trial end. |
| R-05 | Rate limiting on proposal submission is out of scope for v1 internal trial. If usage expands beyond internal trial without re-evaluation, spam/abuse risk is unaddressed. | Medium | Re-evaluate before any public-facing deployment. |
| R-06 | No privacy/regulatory review has been performed. Trial must not transition to production without this review. | High | Release-blocking for production. |
| R-07 | IP address logging in admin_login_log (A-09) may be subject to privacy handling rules depending on applicable regulations. | Low | Confirm or remove IP logging as part of the pre-production privacy/regulatory review. |

---

## 14. ADRs Required

All prerequisite human decisions are now resolved. The following ADR topics must be addressed in the basic design phase. ADRs should be created as Proposed drafts, reviewed, and accepted before implementation begins.

| ADR Topic | Key Decisions to Capture |
|---|---|
| Authentication strategy | Admin email + password; server-side session; HTTP-only cookie; session expiry; hashing algorithm; failed login / lockout behavior; logout / session invalidation |
| Authorization model | Unauthenticated general user vs. authenticated admin; access control boundaries per FR-AC-01 through FR-AC-04 |
| Technology stack | Django 5.x + PostgreSQL 16 + Docker Compose; rationale; package version constraints |
| Database and Docker Compose persistence | Named volume design; data durability; backup mechanism; encryption approach |
| Audit log policy | What is logged (status changes, login events); what is prohibited (proposal body, submitter info, passwords, session tokens); log retention |
| Data retention and operational deletion procedure | 90-day post-trial retention; 14-generation encrypted daily backup; post-retention operational deletion steps |

---

## 15. Document History

| Date | Author | Change |
|---|---|---|
| 2026-05-11 | AI Designer (Claude) | Initial draft created |
| 2026-05-11 | AI Designer (Claude) | HD-01 through HD-19 incorporated from human decisions; AI proposals added for HD-03-AI, HD-13-AI, HD-15-AI; data model outline, Docker Compose environment design, and technology stack proposal added; auto-fixable Design Review findings applied |
| 2026-05-11 | Human + AI Designer | HD-03-AI, HD-13-AI, HD-15-AI approved by human. All HD items are now resolved. Section 4.1 authentication requirements updated; Section 6 stack section updated to Decided; out-of-scope list updated (password reset UI, admin registration UI); NFR-08 updated; risks and ADR section updated accordingly. Auto-fixable Design Review finding applied: Section 7 data model label clarified (preliminary outline, not a pending approval item). |
| 2026-05-11 | System Owner (human) | Requirements document approved. Status changed to Approved. |

---

*This document has been approved by the System Owner on 2026-05-11. It may be used as the basis for basic design. Implementation must not begin until basic design approval and ADR acceptance are also recorded.*
