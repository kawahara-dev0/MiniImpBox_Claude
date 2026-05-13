# Implementation Record — Step 8: Backup Script

## Metadata

| Field | Value |
|---|---|
| Roadmap step | Phase 4, Step 8 — Backup script |
| Implementation request | docs/implementation/implementation-request-v1.md |
| Roadmap | docs/design/roadmap-v1.md |
| Date | 2026-05-12 |
| Builder | AI Builder (Claude, Cowork mode) |
| Risk classification | **Medium** — backup correctness; key management is operational risk, not code risk |
| TDD required | No — Medium-risk step; backup script has no automated test infrastructure in this environment |
| Status | Pending Implementation Reviewer sign-off |

---

## 1. Scope

Step 8 implements `scripts/backup.sh` — a GPG AES-256 symmetric encrypted PostgreSQL backup script with 14-generation rotation.

**In scope (per roadmap-v1.md Step 8):**

- `scripts/backup.sh`: GPG AES-256 symmetric encryption, 14-generation rotation, `set -euo pipefail`
- Script is executable (`chmod +x`)
- Rotation logic handles zero existing files (no error on first run)
- `.env.example`: `BACKUP_GPG_PASSPHRASE` comment and `docker compose down --volumes` destructive warning — already present from Step 1

**Out of scope:**

- Test coverage CSV (Step 9)
- Lint run (Step 9)

---

## 2. Changed Files

| File | Action | Rationale |
|---|---|---|
| `scripts/backup.sh` | Created | GPG AES-256 backup per basic design Section 14 and ADR-006 |
| `.env.example` | No change | `BACKUP_GPG_PASSPHRASE` comment and destructive warning already present from Step 1 |
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated | Rows S8-1 through S8-6 added |

---

## 3. Implementation Notes and Assumptions

**SD-01 (Assumption): Script matches basic design Section 14 exactly**

`scripts/backup.sh` is implemented exactly as specified in basic design Section 14. No deviations. Key behaviors:
- `set -euo pipefail` — script exits on any error, unset variable, or pipe failure
- `.env` sourced if present (using `set -a` / `set +a` for export)
- Backup named `backup_YYYYMMDD_HHMMSS.sql.gz.gpg`
- `pg_dump` inside `db` container piped through `gzip` on host, then encrypted with GPG `--passphrase-fd 3` (avoids passphrase in process list)
- Rotation: `ls -t ... | tail -n +15` selects files beyond 14; `rm` removes them
- `mapfile` used for safe array assignment from command output

**SD-02 (Assumption): Zero-file rotation is handled safely**

When no backup files exist, `ls -t "${BACKUP_DIR}"/backup_*.sql.gz.gpg 2>/dev/null` returns empty (2>/dev/null suppresses "no such file" error). `tail -n +15` on empty input also returns empty. `mapfile` produces an empty array. The `if [ "${#OLD_FILES[@]}" -gt 0 ]` guard prevents `rm` from executing with an empty list. No rotation error on first run.

**SD-03 (Assumption): `BACKUP_GPG_PASSPHRASE` passed via file descriptor 3 (not env var or args)**

`--passphrase-fd 3` reads the passphrase from file descriptor 3 (`3< <(printf '%s' "$BACKUP_GPG_PASSPHRASE")`). This prevents the passphrase from appearing in the process list (`ps aux`). The passphrase is in the process environment but not in command arguments.

**SD-04 (Assumption): Script runs from the project root where docker-compose.yml lives**

`docker compose exec` requires the Docker Compose project context. The script should be run from the project root directory (same directory as `docker-compose.yml`). The `BACKUP_DIR` default (`./backups`) is relative to the working directory.

**SD-05 (Assumption): Automated backup tests not feasible in this environment**

Automated testing of backup correctness requires:
- A running Docker Compose stack with the `db` container
- GPG installed on the host
- Write access to `./backups/`

These cannot be validated by `pytest` in the Django container. Backup correctness is verified by human verification in Gate 4 (S8-3 through S8-6). Syntax validity is confirmed by `bash -n` (S8-1) and executable permission by `ls -la` (S8-2).

---

## 4. Checks Run

| Check | Result | Notes |
|---|---|---|
| `bash -n scripts/backup.sh` — syntax check | Pass | Exit code 0; no syntax errors |
| `ls -la scripts/backup.sh` — executable permission | Pass | `-rwxr-xr-x` confirmed |
| Static review against basic design Section 14 | Pass | Script matches reference implementation exactly |
| ADR-004 and ADR-006 compliance review | Pass | See Section 8 |
| Full test suite (119 tests) — regression check | Pass | `119 passed` — no regressions (backup script adds no Django code) |
| Lint (flake8/ruff) | Not run | Not installed; shell script lint deferred; `bash -n` covers syntax |
| CI | Not configured | Not configured for this project |

---

## 5. Test Case CSV Status

| File | Status |
|---|---|
| `docs/tests/miniimpbox_v1_test_cases.csv` | Updated — rows S8-1 through S8-6 added |

**S8-1, S8-2** (Automated/CLI, AI): Pass — confirmed at implementation time.
**S8-3 through S8-6** (Human, Release-blocking Gate 4): Pending — require running Docker Compose stack with GPG.

---

## 6. Implementation Reviewer Outcome

**Reviewer:** AI Implementation Reviewer (Claude, Cowork mode) — independent of Builder

**Review date:** 2026-05-12

### Scope reviewed

- `scripts/backup.sh`
- `docs/tests/miniimpbox_v1_test_cases.csv` rows S8-1 through S8-6
- Implementation record Sections 1–5
- Compliance against: basic design Section 14, ADR-004, ADR-006

### Findings

**Finding R1 — Non-blocking — No automated test for rotation count**

Rotation logic correctness (exactly 14 files retained after 15 runs) cannot be tested without a live stack and GPG. This is documented in SD-05 and covered by Gate 4 manual verification (S8-5). Acceptable — the logic is straightforward `ls -t | tail -n +15` and the Gate 4 verification will confirm it in the actual environment.

Classification: Non-blocking. Covered by Gate 4.

**Finding R2 — Non-blocking — `mapfile` requires bash (not sh)**

The shebang is `#!/usr/bin/env bash` and `mapfile` is a bash built-in. The script is bash-specific and correct. WSL2 hosts have bash available. No issue.

Classification: Non-blocking (informational).

### Behavior compliance review

| Acceptance criterion | Implementation | Match |
|---|---|---|
| GPG AES-256 symmetric encryption | `--cipher-algo AES256 --symmetric` | ✓ |
| 14-generation rotation | `ls -t | tail -n +15` + `rm` | ✓ |
| Zero-file rotation: no error | `2>/dev/null` + empty array guard | ✓ |
| Passphrase not in process args | `--passphrase-fd 3` | ✓ |
| `set -euo pipefail` | Line 2 | ✓ |
| File named `backup_YYYYMMDD_HHMMSS.sql.gz.gpg` | `date +%Y%m%d_%H%M%S` | ✓ |
| Backup written to `./backups/` (bind mount) | `BACKUP_DIR="${BACKUP_DIR:-./backups}"` | ✓ |
| Script executable | `chmod +x` confirmed | ✓ |

### Security review

- Passphrase passed via `--passphrase-fd 3` — not in process arguments ✓
- Passphrase loaded from `.env` or environment — not hardcoded ✓
- `.env.example` warns about storing passphrase separately ✓
- Backup files encrypted before write — no plaintext backup file created ✓
- Rotation deletes only `backup_*.sql.gz.gpg` pattern — no unintended deletion ✓

### Test adequacy review

S8-1 (syntax) and S8-2 (executable) are the only automated/CLI checks possible for a shell backup script in this environment. S8-3 through S8-6 are correct Gate 4 manual items. Test adequacy is acceptable for a Medium-risk operational script with no Django code.

### Overall finding

**No blocking findings.** Step 8 is ready to commit and push. Gate 4 covers backup restore verification (release-blocking, not phase-blocking).

---

## 7. Tester Outcome

**Tester used:** No — Medium-risk step. IMPLEMENTATION_WORKFLOW.md requires Tester for High-risk items. Step 8 is Medium-risk (backup correctness; key management is operational risk).

**Reviewer test adequacy review:** Performed in Section 6 above. Automated checks limited to syntax and executable permission. Gate 4 manual items cover functional backup correctness.

---

## 8. Human Verification Items

| ID | Item | Classification | Status |
|---|---|---|---|
| HV-S8-1 | Run backup once — verify encrypted file created (S8-3) | Release-blocking (Gate 4) | Pending |
| HV-S8-2 | Run backup when no files exist — verify no rotation error (S8-4) | Release-blocking (Gate 4) | Pending |
| HV-S8-3 | Run backup 15 times — verify exactly 14 files remain (S8-5) | Release-blocking (Gate 4) | Pending |
| HV-S8-4 | Decrypt and restore a backup — verify data intact (S8-6) | Release-blocking (Gate 4) | Pending |

**Gate note:** Human Gate 4 is release-blocking before trial start. These items are NOT phase-blocking within Phase 4 — Step 9 may proceed without Gate 4.

---

## 9. Assumptions and Remaining Risks

| ID | Type | Description |
|---|---|---|
| SD-01 | Assumption | Script matches basic design Section 14 exactly |
| SD-02 | Assumption | Zero-file rotation handled safely by empty array guard |
| SD-03 | Assumption | Passphrase via `--passphrase-fd 3` prevents exposure in process list |
| SD-04 | Assumption | Script run from project root directory |
| SD-05 | Assumption | Automated backup tests not feasible without live stack + GPG |
| BD-A-09 | Risk | GPG must be installed on host before trial begins |
| R-RM-04 | Risk | Backup passphrase loss renders all backups unrecoverable — store in password manager before trial (Gate 4) |
| BD-02 | Risk | ip_address in AdminLoginLog — release-blocking for trial start |

---

## 10. ADR Compliance Notes

| ADR | Compliance |
|---|---|
| ADR-003 | No new dependencies introduced ✓ |
| ADR-004 | Backup written to `./backups` bind mount; `BACKUP_GPG_PASSPHRASE` in `.env`; `docker compose down --volumes` destructive warning in `.env.example` ✓ |
| ADR-006 | GPG AES-256 symmetric encryption; 14-generation rotation; passphrase not in repository or backup directory ✓ |

---

## 11. Commit Hash

**Commit:** `001691d`

---

## 12. Push Status

**Status:** Pushed to `origin/master`.

---

*This implementation record is produced by the AI Builder. It is traceability evidence, not final acceptance, residual risk acceptance, or release approval.*
