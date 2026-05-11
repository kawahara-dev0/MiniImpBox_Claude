# ADR-002: Authorization Model

## Status

Accepted

Approved by: System Owner (human) — 2026-05-11

---

## Context

Mini Improvement Box v1 has two distinct user types with fundamentally different access levels:

- **General User**: Unauthenticated. May only access the proposal submission form. Cannot access any admin screen, proposal list, proposal detail, status history, or status change operation.
- **Administrator User**: Authenticated. May access all admin screens: proposal list, individual proposal detail with status history, and status change operations.

The following constraints apply:

- No dual-role design: a single account cannot be both a general user and an administrator simultaneously (HD-02).
- General users are anonymous and not stored in any user table. There is no general user account concept in v1.
- Access control boundaries must be enforced at the server side. Client-side restrictions alone are not sufficient.
- The technology stack is Django 5.x (ADR-003).
- Only one admin role exists in v1. No fine-grained permission levels within the administrator role are required.
- Filter/sort, comments, and proposal deletion are out of scope for v1 — their authorization is not applicable.

The authorization model must be simple, auditable, and correctly enforce the boundary between unauthenticated access and authenticated administrator access.

---

## Decision

v1 uses a **two-tier authorization model**:

**Tier 1 — Unauthenticated access (General User)**
- Permitted: proposal submission form (`GET /` or `/submit/`) and proposal submission POST.
- Denied: all other URLs. Unauthenticated requests to protected URLs are redirected to the login page (or return HTTP 403 for non-browser clients).

**Tier 2 — Authenticated Administrator access**
- Permitted: all admin views (proposal list, proposal detail, status change).
- Enforced using Django's `@login_required` decorator or equivalent middleware on all admin views.
- Administrator identity is determined by Django's `is_staff` flag or an equivalent boolean attribute on the user model. The specific field to use (Django built-in `is_staff` vs. a custom `is_admin` field) will be decided in basic design.
- No permission table, no role table, and no RBAC framework is used in v1.

**Shared rules:**
- Authorization checks are performed server-side on every request to a protected endpoint.
- There is no client-side-only access restriction. The server must enforce access control independently of any UI state.
- Authorization logic must not be duplicated across views. A shared decorator, mixin, or middleware must be used for all admin-protected views.

---

## Alternatives Considered

**A. Django's built-in permissions system (object-level or model-level permissions)**
Django includes a permission framework with `Permission` model and `has_perm()` checks. For v1's two-role model with no fine-grained permissions, this adds unnecessary complexity. The simpler `is_staff` or `@login_required` approach is sufficient.

**B. Full RBAC (Role-Based Access Control) with a role table**
Appropriate when multiple distinct roles with different permission sets are needed. v1 has only one admin role — RBAC would be over-engineering at this stage.

**C. ABAC (Attribute-Based Access Control)**
More expressive than RBAC but significantly more complex to implement and maintain. Unjustifiable for a two-role v1 system.

**D. Manual per-view authentication check**
Each view independently checks `request.user.is_authenticated`. This duplicates authorization logic and creates risk of accidentally missing the check in a new view. A shared decorator/middleware is safer.

---

## Reasons

- **Simplest model that correctly satisfies requirements.** Two distinct roles with a clear boundary. No inter-admin permission differences. No need for a permission table.
- **Django's `@login_required` and `is_staff`/`is_authenticated` are well-tested.** Using the framework's built-in mechanisms reduces implementation risk and is consistent with ADR-003 (Django stack selection).
- **Centralized authorization logic** (shared decorator or middleware) reduces the risk of a new admin view accidentally skipping the authentication check.
- **Server-side enforcement** is the correct security boundary. Client-side restrictions (e.g., hiding nav links) are UX only and must not be the sole access control mechanism.
- **No dual-role design needed.** General users are anonymous; there is no user record to associate a role with. The distinction is simply: authenticated = admin, unauthenticated = general user.

---

## Consequences

**Positive:**
- Simple to implement and understand.
- Low risk of authorization bypass if a shared decorator/middleware is used consistently.
- No additional tables or configuration needed beyond Django's built-in user model.
- Easy to test: unauthenticated access to admin URLs must always be redirected or denied.

**Negative:**
- No granularity within the administrator role. If v2 needs a read-only admin or a super-admin role, the model must be extended. The refactoring required is modest (add a permission check or extend the user model) but it is still a breaking change to the current model.
- The specific admin identification attribute (`is_staff` vs. custom field) is deferred to basic design. If the wrong attribute is chosen, migration effort is required.

---

## Related Requirements

- FR-AC-01: Unauthenticated users may only access the proposal submission form.
- FR-AC-02: Admin screens are not accessible to unauthenticated users.
- FR-AC-03: No inter-user proposal visibility for general users (proposals not linked to user accounts).
- FR-AC-04: Authenticated administrators cannot access other administrators' credentials or session data.
- HD-02: Two distinct roles; no dual-role.
- HD-07: Access control boundaries.
- ADR-001: Authentication strategy (Django session auth).
- ADR-003: Technology stack (Django 5.x).
- SECURITY_POLICY.md: Authorization must not be weakened; permission checks must be consistent.

---

## Notes

- The specific field used to identify administrators (`is_staff`, `is_superuser`, or a custom field) must be decided in basic design. The decision should be consistent with the seed/management script (ADR-001) and must not accidentally grant admin access to non-admin accounts.
- If v2 introduces a read-only admin role or a super-admin role, this ADR should be revisited and a RBAC or permission-based model evaluated.
- All admin views must be enumerated in the basic design to confirm that the `@login_required` decorator or equivalent is applied consistently. This must be verified in implementation review and access control tests.
