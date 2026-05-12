# ADR-004: Database Persistence and Docker Compose Environment Design

## Status

Accepted

Approved by: System Owner (human) — 2026-05-11

---

## Context

Mini Improvement Box v1 uses Docker Compose for development and trial verification (HD-15-AI, NFR-06, NFR-07). The following requirements apply to the environment design:

- Database data files must not be stored only in ephemeral container storage. A named Docker volume or host-mounted path must be used for the database (HD-15-AI, NFR-07).
- Backup files must also be written to a durable location outside ephemeral container storage (HD-15-AI, NFR-07).
- Daily backups are required during the trial period with 14 backup generations retained and backup encryption required (HD-17).
- All credentials (DB password, Django secret key, admin seed credentials) must not be committed to the repository. They must be passed via `.env` file or equivalent mechanism (SECURITY_POLICY.md, HD-01).
- This environment design covers development and trial verification only. It is **not** production release or production operation approval (HD-15-AI).
- The application must be able to continue operating after container recreation without losing data.
- The technology stack is Django 5.x + PostgreSQL 16 (ADR-003).

The environment design must be simple to operate for a limited internal trial while meeting data durability and backup security requirements.

---

## Decision

### Docker Compose Service Structure

The Docker Compose configuration defines the following services:

**`app` service**
- Django application container.
- Stateless: no application-level data is stored inside the container. All persistent data is in the database.
- Depends on the `db` service being healthy before starting.
- Receives all secrets (DB password, Django `SECRET_KEY`, admin credentials) via environment variables sourced from a `.env` file.

**`db` service**
- PostgreSQL 16 container.
- Database data stored in a **named Docker volume** (e.g., `pgdata`). This volume persists across container recreation (`docker compose down` without `--volumes`).
- The `pgdata` volume must be defined in the `volumes:` section of `docker-compose.yml` (named volume, not an anonymous volume).
- DB credentials passed via environment variables from `.env`.

**Backup mechanism**
- Backup execution: a `pg_dump` command run on a schedule. The specific mechanism (cron job in a separate `backup` service container, or a host-level cron calling `docker exec`, or a Django management command triggered by cron) will be decided in basic design.
- Backup destination: a **host-mounted directory** (bind mount) accessible outside the container lifecycle (e.g., `./backups:/backups` or an absolute host path). Backup files must survive container recreation and removal.
- Backup encryption: each backup file must be encrypted before or during write. The specific encryption tool (GPG symmetric encryption, `age`, or `openssl enc`) and key management procedure will be defined in basic design and operational procedure documentation.
- Backup retention: at least 14 daily backup files are retained. Older files beyond the 14-generation limit are deleted by the backup script. The deletion must be part of the backup script, not a separate manual step.
- Backup file naming: include date in filename (e.g., `backup_YYYYMMDD.sql.gz.gpg`) to support rotation logic.

### Secrets Management

- A `.env` file at the project root provides all secrets to Docker Compose via `env_file:` or `environment:` directives.
- `.env` is listed in `.gitignore` and must never be committed to the repository.
- A `.env.example` file (with placeholder values, no real secrets) is committed to the repository as a setup guide.
- Required secrets: `POSTGRES_PASSWORD`, `DJANGO_SECRET_KEY`, `DJANGO_ADMIN_EMAIL`, `DJANGO_ADMIN_PASSWORD` (for seed script), and any backup encryption key reference.

### Data Durability Guarantee

The following operations must **not** cause data loss:
- `docker compose down` followed by `docker compose up` (named volume preserved).
- Rebuilding the `app` container image.
- Updating application code and redeploying.

The following operation **will** cause data loss and must be explicitly documented as destructive:
- `docker compose down --volumes` (removes named volumes). This must never be run without intent to destroy all data.

---

## Alternatives Considered

**A. Anonymous Docker volume for the database**
Anonymous volumes are created automatically but are harder to manage, may not be preserved reliably across `docker compose down`, and are not easily identified or backed up. Named volumes are explicit and manageable.

**B. Bind mount for the database data directory (host path)**
A bind mount to a host path (e.g., `./data/postgres`) is an alternative to a named volume. It is more transparent (the files are visible on the host directly) but has permission complexity on Linux hosts. Named volumes are the Docker-recommended approach for database data. Both approaches are acceptable; named volume is the default choice.

**C. Backup files in a second named volume**
Backup files could be stored in a named Docker volume rather than a host bind mount. However, a host bind mount is preferable because it makes backup files directly accessible on the host filesystem without requiring `docker exec` or `docker cp` to retrieve them. This simplifies recovery.

**D. Managed cloud database (e.g., AWS RDS, Cloud SQL)**
Out of scope for v1 limited internal trial. Adds cost and external service dependency.

**E. SQLite with file volume**
Simpler than PostgreSQL. However, SQLite does not support `pg_dump`, has weaker concurrency guarantees, and is less production-representative. PostgreSQL is preferred per ADR-003.

---

## Reasons

- **Named Docker volumes** are the recommended, stable mechanism for persisting database data across container lifecycles in Docker Compose. They are explicitly managed and not accidentally deleted by normal `docker compose down`.
- **Host bind mount for backups** makes backup files directly accessible on the host filesystem without requiring Docker commands. This simplifies backup retrieval, verification, and transfer to off-system storage.
- **Backup encryption** is required because backup files may contain personal data (proposal body, submitter information) and admin credentials are in the database. Encrypting backup files limits exposure if the backup directory is accessed by an unauthorized party.
- **14-generation daily backup retention** provides approximately two weeks of recovery window, which is a reasonable baseline for a limited internal trial.
- **`.env` file for secrets** is a standard Docker Compose practice. It is simple, does not require a secrets manager, and keeps credentials out of the repository.

---

## Consequences

**Positive:**
- Database data survives normal container recreation.
- Backup files are accessible on the host without Docker commands.
- Backup encryption limits data exposure risk in backup files.
- Secrets are not committed to the repository.
- The environment is simple to start and stop with `docker compose up/down`.

**Negative:**
- The backup encryption key must be stored securely on the host. If the key is lost, encrypted backups cannot be recovered. Key management procedure must be defined in the operational procedure documentation.
- The `.env` file on the host contains all secrets. Access to the host must be restricted to authorized operators.
- 14 daily backup generations assume a single backup per day. If multiple backups are taken per day, the rotation logic must be adjusted.
- `docker compose down --volumes` is destructive and must be explicitly documented and prevented in normal operations. This is an operational risk if operators are unfamiliar with Docker Compose volume flags.

---

## Related Requirements

- NFR-06: Application must run in Docker Compose for development and trial verification.
- NFR-07: Database data files and backup files must not be stored only in ephemeral container storage.
- HD-15, HD-15-AI: Docker Compose environment design approved (human approved 2026-05-11). Not production release/operation approval.
- HD-17: Daily backups, 14 generations, backup encryption required, 90-day post-trial data retention.
- SECURITY_POLICY.md: Secrets must not be committed; sensitive data must be protected.
- ADR-003: Technology stack (Django 5.x + PostgreSQL 16).

---

## Notes

- The specific backup encryption tool (GPG, `age`, `openssl enc`) and key management procedure (where the key is stored, how it is rotated, how recovery is performed) must be defined in basic design and operational procedure documentation before the trial begins.
- The backup script and the rotation logic (deleting backups older than 14 generations) must be tested before the trial begins.
- Restoring from backup must be tested at least once in the trial environment before relying on it. The restore procedure must be documented.
- This design covers development and trial verification only. Production deployment, if it occurs, requires a separate environment design review and potentially a managed database service with built-in backup.
- `docker compose down --volumes` must be documented as a destructive operation. A warning should be added to the operational runbook.
