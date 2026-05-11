# ADR-003: Technology Stack Selection

## Status

Accepted

Approved by: System Owner (human) — 2026-05-11

---

## Context

Mini Improvement Box v1 is a small-scale, limited internal trial web application. A technology stack must be selected before implementation begins.

The selection criteria, as specified in HD-13-AI (human approved 2026-05-11), are:

- **v1 requirements**: form-based proposal submission, server-side admin interface, session-based authentication, proposal status management, status change history, audit logging.
- **Limited internal trial scope**: no high-load, no public-facing operation, small number of users and proposals.
- **Implementation ease**: reach a working, testable prototype quickly with minimal infrastructure setup.
- **Authentication and authorization robustness**: the auth module is the highest-risk component; the stack should provide tested, maintained auth primitives.
- **Data persistence**: reliable DB access with migration tooling.
- **Test ease**: the stack must support automated unit and integration testing.
- **Docker Compose verification ease**: the full stack must run in Docker Compose for development and trial verification.
- **Maintainability**: code should be understandable and maintainable by a developer unfamiliar with the original implementation.

The selected stack (Option A: Django + PostgreSQL + Docker Compose) was proposed by the AI Designer and approved by the human in HD-13-AI.

---

## Decision

### Language and Runtime

**Python 3.12+**

Specific minor version to be locked in `pyproject.toml` or `requirements.txt` in basic design.

### Web Framework

**Django 5.x** (latest stable 5.x release at time of implementation)

- Server-side rendering with Django templates (no separate frontend framework or build pipeline).
- Django's built-in URL routing, view layer, form validation, and template engine.
- No Django REST Framework in v1. All interactions are form-based HTML.

### ORM and Migrations

**Django ORM with built-in migration tooling**

- Models defined as Django model classes.
- Migrations generated and applied with `manage.py makemigrations` and `manage.py migrate`.
- No additional ORM (SQLAlchemy) or migration tool (Alembic) in v1.

### Authentication

**Django's built-in authentication framework** (see ADR-001)

- `django.contrib.auth` for user model, session management, login/logout views.
- HTTP-only session cookie.
- Password hashing via Django's default hasher (PBKDF2-SHA256) or configured to bcrypt.

### Database

**PostgreSQL 16** (latest stable 16.x at time of implementation)

- Accessed via `psycopg` (psycopg3) or `psycopg2`; specific driver to be decided in basic design.
- Named Docker volume for data persistence (ADR-004).

### Test Framework

**pytest + pytest-django**

- Unit tests for models, form validation, and business logic.
- Integration tests for view behavior, access control, and status transitions.
- Test database separate from development database.

### Containerization

**Docker Compose** for development and trial verification environment (ADR-004).

### Static Files

Django's static file serving (`whitenoise` or equivalent) for development/trial. Specific approach in basic design.

### Specific package versions

Package versions (Django minor version, psycopg version, pytest-django version, etc.) will be locked in `requirements.txt` or `pyproject.toml` in basic design and must not be changed without a corresponding review.

---

## Alternatives Considered

**Option B: FastAPI + Jinja2 + SQLAlchemy + Alembic**
More flexible for future API-first design. However, it requires manual implementation of session-based authentication and password hashing, which increases implementation risk for the highest-risk component (auth). Suitable if the team plans an API-first architecture from the start.

**Ruby on Rails + PostgreSQL**
Full-stack, batteries-included, similar philosophy to Django. However, Python is preferred for consistency with the team's ecosystem and tooling (assumed). Rails would be appropriate if the team's primary language is Ruby.

**Node.js (Express or NestJS) + PostgreSQL**
Appropriate for a JavaScript-first team or if a REST + SPA architecture is desired. Adds frontend build complexity for a v1 that does not need a SPA. More setup overhead for session-based auth and form-based rendering.

**Django + SQLite**
SQLite is simpler to set up and has no separate database service. However, it is less production-representative, has weaker concurrency handling, and backup tooling (`pg_dump`) is not available. PostgreSQL is preferred for a trial that should resemble a production-like data environment.

---

## Reasons

- **Django provides batteries-included authentication** that is actively maintained and security-reviewed. This directly reduces implementation risk for the most security-sensitive component of v1 (admin authentication).
- **Server-side rendering eliminates frontend build complexity.** For a v1 limited internal trial with a simple form-based UI, Django templates are sufficient. No npm, webpack, or separate React/Vue build is needed.
- **Django ORM with built-in migrations** reduces the number of tools to learn and maintain. Migrations are tightly integrated with the model layer.
- **PostgreSQL is production-representative.** It is more suitable as a trial environment database than SQLite, provides stronger data integrity constraints, and supports `pg_dump` for structured backups.
- **pytest + pytest-django** provides a well-supported testing environment with database fixture support and Django-specific utilities.
- **Docker Compose** is a standard tool for defining multi-service development and trial environments with a single configuration file.

---

## Consequences

**Positive:**
- Fast time-to-working-prototype. Django's auth, ORM, and template system cover the majority of v1's needs out of the box.
- Well-documented and widely used framework; maintainers and future developers are likely familiar with it.
- Strong security baseline in the auth and session subsystem.
- Test tooling is straightforward and well-integrated.

**Negative:**
- Django is more opinionated than FastAPI. If the architecture needs to pivot to API-first (e.g., for a mobile client in v2), Django REST Framework would need to be added, or the framework reconsidered.
- Server-side rendering only. No React/Vue components without additional frontend tooling.
- Django's monolithic structure may feel heavyweight for a very small application, but this is an acceptable tradeoff for v1's internal trial scope.
- Package version lock-in: upgrading Django major versions (e.g., 5.x → 6.x) may require code changes. This is a normal lifecycle cost.

---

## Related Requirements

- HD-13, HD-13-AI: Technology stack decision (human approved 2026-05-11).
- HD-12: Limited internal trial; no large-scale operation.
- HD-15, HD-15-AI: Docker Compose environment design.
- NFR-06: Application must run in Docker Compose.
- NFR-08: Technology stack decided and approved.
- ADR-001: Authentication strategy (Django built-in auth).
- ADR-002: Authorization model (Django login_required).
- ADR-004: Database persistence (PostgreSQL + Docker Compose).

---

## Notes

- Specific package versions must be locked in `requirements.txt` or `pyproject.toml` in basic design. Dependencies must not be pinned to a range that allows silent upgrades.
- If v2 requires a REST API or mobile client, Django REST Framework (DRF) can be added without replacing the framework. If a full SPA frontend is required, the architecture should be reconsidered.
- Re-evaluate this decision if the team's primary language or preferred tooling changes significantly before v2.
