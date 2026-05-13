# Mini Improvement Box

A small-scale web application for collecting and managing improvement proposals.

General users submit proposals without authentication. Administrators review and manage them through a password-protected portal.

v1 is scoped as a limited internal trial and is not intended for public or production release.

---

## Features

**General users (unauthenticated)**

- Submit improvement proposals (title, body, optional name and contact)
- Receive a submission confirmation page

**Administrators (authenticated)**

- Log in with email and password
- Browse all proposals (paginated, newest first)
- View proposal detail and status history
- Change proposal status (New → Reviewing → Planned → Done / Declined)
- Log out

---

## Tech Stack

| Component | Version |
|---|---|
| Python | 3.12 |
| Django | 5.2 |
| PostgreSQL | 16 |
| Gunicorn | 23 |
| WhiteNoise | 6.7 |
| Docker Compose | v2 |

---

## Project Structure

```
miniimpbox/
├── config/               Django project settings, URLs, WSGI
├── proposals/            Proposal models, forms, views, templates, tests
├── accounts/             Admin auth backend, login/logout views, AdminLoginLog, tests
│   └── management/commands/seed_admin.py
├── templates/            Shared base template
├── scripts/
│   └── backup.sh         Encrypted PostgreSQL backup script
├── docs/
│   ├── requirements/     Approved requirements
│   ├── design/           Basic design, roadmap
│   ├── adr/              Architecture Decision Records (ADR-001 – ADR-006)
│   ├── implementation/   Step records, human gate decisions
│   └── tests/            Test case CSV, coverage CSV
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Quick Start

### Prerequisites

- Docker and Docker Compose v2
- Git

### 1. Clone and configure environment

```bash
git clone <repository-url>
cd miniimpbox
cp .env.example .env
```

Edit `.env` and set:

| Variable | Description |
|---|---|
| `DJANGO_SECRET_KEY` | Long random string |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames (e.g. `localhost,127.0.0.1`) |
| `POSTGRES_PASSWORD` | Database password |
| `DJANGO_ADMIN_EMAIL` | Initial administrator email |
| `DJANGO_ADMIN_PASSWORD` | Initial administrator password |
| `BACKUP_GPG_PASSPHRASE` | Passphrase for encrypted backups — store separately in a password manager |

> **Warning:** Do not commit `.env`. Store `BACKUP_GPG_PASSPHRASE` in a password manager, not only in `.env`.

### 2. Start the application

```bash
docker compose up --build
```

This runs database migrations and starts Gunicorn on port 8000 automatically.

### 3. Seed the administrator account

```bash
docker compose exec app python manage.py seed_admin
```

Uses `DJANGO_ADMIN_EMAIL` and `DJANGO_ADMIN_PASSWORD` from `.env`.

### 4. Access the application

| Surface | URL |
|---|---|
| Proposal submission (public) | http://localhost:8000/ |
| Admin login | http://localhost:8000/admin-portal/login/ |
| Admin proposal list | http://localhost:8000/admin-portal/proposals/ |

---

## Running Tests

Install development tools inside the running container:

```bash
docker compose exec app pip install flake8 pytest-cov
```

Run the test suite:

```bash
docker compose exec app pytest
```

Run lint:

```bash
docker compose exec app flake8 accounts/ proposals/ config/
```

Run coverage (High-risk modules):

```bash
docker compose exec app pytest --cov=accounts --cov=proposals --cov-report=term-missing
```

> Development tools (flake8, pytest-cov) are not in `requirements.txt` (runtime-only).
> Re-install them after container rebuild.

---

## Backup

The backup script creates a GPG-encrypted PostgreSQL dump and retains up to 14 generations.

```bash
docker compose exec app bash /app/scripts/backup.sh
```

Backups are written to `./backups/` on the host.

Restore procedure:

```bash
# Decrypt
gpg --batch --passphrase "$BACKUP_GPG_PASSPHRASE" \
    --output dump.sql.gz --decrypt backups/<filename>.sql.gz.gpg

# Restore
gunzip -c dump.sql.gz | docker compose exec -T db \
    psql -U $POSTGRES_USER $POSTGRES_DB
```

> **Warning:** `docker compose down --volumes` destroys the `pgdata` volume and all data. Use `docker compose down` (without `--volumes`) for normal stops.

---

## Architecture Decisions

| ADR | Decision |
|---|---|
| ADR-001 | Email + password authentication, server-side session (HTTP-only cookie) |
| ADR-002 | `is_staff=True` flag identifies administrators; no role table |
| ADR-003 | Django 5.x + PostgreSQL 16 + Docker Compose; no JS framework |
| ADR-004 | PostgreSQL in Docker Compose; named volume for persistence; host bind mount for backups |
| ADR-005 | Audit log policy: `StatusHistory` and `AdminLoginLog` are append-only |
| ADR-006 | No in-app deletion in v1; operational deletion via direct DB procedure only |

Full records: [`docs/adr/`](docs/adr/)

---

## Documentation

| Document | Path |
|---|---|
| Requirements | [docs/requirements/requirements-v1.md](docs/requirements/requirements-v1.md) |
| Basic Design | [docs/design/basic-design-v1.md](docs/design/basic-design-v1.md) |
| Roadmap | [docs/design/roadmap-v1.md](docs/design/roadmap-v1.md) |
| Implementation Records | [docs/implementation/](docs/implementation/) |
| Test Cases | [docs/tests/miniimpbox_v1_test_cases.csv](docs/tests/miniimpbox_v1_test_cases.csv) |
| Coverage | [docs/tests/coverage_result.csv](docs/tests/coverage_result.csv) |
| AI Development Policy | [docs/ai-development/](docs/ai-development/) |

---

## Development Status

v1 implementation is complete (Steps 1–9, Gates 1–3 cleared).

Gate 4 (trial readiness) remains **release-blocking** and has not been cleared.
The system must not be released to external users or moved to production until Gate 4 is completed and the System Owner accepts residual risks.

Pending release-blocking items:

- `ip_address` logging in `AdminLoginLog` — privacy review required (BD-02)
- Backup passphrase storage confirmation before trial start
- Final manual verification of all user-facing flows
- System Owner residual risk acceptance and release decision
