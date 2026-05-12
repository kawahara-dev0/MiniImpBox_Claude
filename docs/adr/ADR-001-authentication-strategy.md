# ADR-001: Administrator Authentication Strategy

## Status

Accepted

Approved by: System Owner (human) — 2026-05-11

---

## Context

Mini Improvement Box v1 requires two distinct access patterns:

- **General users** submit improvement proposals without any authentication. They are anonymous and unauthenticated.
- **Administrator users** access a proposal management interface that includes browsing, viewing details, status change history, and changing proposal statuses. This interface must be protected.

The following constraints apply:

- v1 is a limited internal trial, not a public-facing service.
- No external identity provider is available or required.
- The system must not store passwords in plaintext.
- Failed login attempts must not reveal whether an email address exists (security baseline, SECURITY_POLICY.md).
- Administrator login success and failure events must be auditable (HD-19).
- No public self-registration, admin registration UI, or password reset UI is in scope (HD-03-AI, HD-04).
- Administrator accounts are pre-created via seed script or management script (HD-01).
- The technology stack is Django 5.x (ADR-003, HD-13-AI).

The authentication mechanism must be: secure for an internal trial, self-contained (no external dependencies), auditable, and implementable with minimal custom code.

---

## Decision

Administrators authenticate using **email address and password** managed by Django's built-in authentication framework.

Sessions are maintained using **server-side sessions** transmitted via an **HTTP-only cookie**.

Specific design parameters to be defined in basic design:

- Session storage backend (database-backed or cache-backed)
- Session expiry policy (idle timeout and absolute session lifetime)
- Failed login behavior (error message wording, optional lockout after N consecutive failures)
- Logout behavior (server-side session invalidation on logout)
- Password hashing algorithm (Django default: PBKDF2-SHA256; may be configured to bcrypt)
- Admin account seed procedure (credential input via environment variable; not committed to repository)

---

## Alternatives Considered

**A. External OAuth 2.0 / OIDC provider (e.g., Google, GitHub)**
Requires an external service dependency. Not appropriate for a self-contained limited internal trial. Adds setup complexity and external account dependency for a small number of administrators.

**B. Magic link (passwordless email)**
Requires an outbound email service. No email service is in scope for v1. Adds infrastructure dependency with no benefit over email + password for an internal trial.

**C. HTTP Basic Authentication**
Stateless, simple, but credentials are sent with every request. Browser dialog is not user-friendly. Session-based approach is more appropriate for a web application admin interface.

**D. Token-based authentication (JWT stored in localStorage)**
JWTs in localStorage are vulnerable to XSS. Server-side sessions with HTTP-only cookies are a safer baseline for a server-rendered web application.

---

## Reasons

- **Django's built-in session auth is battle-tested.** The authentication subsystem has been maintained and security-reviewed by the Django project over many years. Using it reduces implementation risk significantly compared to building a custom auth mechanism.
- **No external service dependency.** A self-contained v1 limited internal trial should not depend on external identity providers that could be unavailable or require additional configuration.
- **HTTP-only cookie prevents JavaScript access to session tokens.** This is the appropriate baseline for a server-side rendered application, reducing XSS-based session hijacking risk.
- **Server-side session invalidation on logout** ensures that logging out actually ends the session, unlike client-side token approaches where the token may continue to be valid until expiry.
- **Audit logging is straightforward.** Login success and failure can be logged at the authentication view layer without complex infrastructure.
- **Password hashing is handled by Django.** PBKDF2-SHA256 (Django default) or bcrypt (configurable) is a well-reviewed, standards-compliant approach.

---

## Consequences

**Positive:**
- Minimal custom authentication code; relies on Django's tested subsystem.
- Auditable: login events can be logged at the view layer.
- Session invalidation on logout provides correct security behavior.
- No external service dependency; fully self-contained.
- Password hashing is managed by the framework.

**Negative:**
- Password management (seed creation, recovery) is the responsibility of the system operator. There is no self-service password reset in v1 — an admin who loses their password requires direct intervention (seed script or management command).
- No SSO or federated identity. If the organization later adopts a centralized identity provider, authentication will need to be rearchitected.
- Session storage in the database adds a DB dependency for every authenticated request unless a cache-backed session backend is used (to be decided in basic design).

---

## Related Requirements

- FR-AUTH-01: General users do not authenticate.
- FR-AUTH-02: Administrators authenticate with email + password.
- FR-AUTH-03: Server-side session, HTTP-only cookie; expiry in basic design.
- FR-AUTH-04: Administrators must be able to log out (session invalidation).
- FR-AUTH-05: Failed login attempts must not expose whether the email address exists.
- FR-AUTH-06: Login success and failure events must be logged.
- FR-AUTH-07: No general user registration UI, admin registration UI, or password reset UI in v1.
- HD-01: Admin accounts created via seed/management script.
- HD-03, HD-03-AI: Email + password authentication approved.
- HD-19: Audit log — admin login success/failure required; no sensitive data in logs.
- SECURITY_POLICY.md: Authentication must not be bypassed; credentials must not be logged.
- ADR-003: Django 5.x is the selected framework.

---

## Notes

- Re-evaluate authentication strategy if v2 expands beyond a closed internal trial (e.g., if multiple organizations use the system or if SSO integration is required).
- If failed login lockout is implemented in basic design, the lockout duration and reset mechanism must be defined to avoid denial-of-service risk against admin accounts.
- The specific session expiry policy (idle timeout, absolute lifetime) is a security-relevant detail that must be explicitly defined in basic design, not left to Django defaults without review.
