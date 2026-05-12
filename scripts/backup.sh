#!/usr/bin/env bash
set -euo pipefail

# Load env vars (if not already in environment)
if [ -f "$(dirname "$0")/../.env" ]; then
  # shellcheck disable=SC1091
  set -a; source "$(dirname "$0")/../.env"; set +a
fi

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATE=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="backup_${DATE}.sql.gz"
ENC_FILE="${DUMP_FILE}.gpg"

mkdir -p "$BACKUP_DIR"

echo "Starting backup: $ENC_FILE"

# Dump and compress inside the db container, pipe through encryption on host
docker compose exec -T db \
  pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" \
  | gzip \
  | gpg --batch --yes --symmetric \
        --cipher-algo AES256 \
        --passphrase-fd 3 \
        --output "${BACKUP_DIR}/${ENC_FILE}" \
        /dev/stdin \
  3< <(printf '%s' "${BACKUP_GPG_PASSPHRASE}")

echo "Backup written: ${BACKUP_DIR}/${ENC_FILE}"

# Rotate: keep only the 14 most recent backup files
mapfile -t OLD_FILES < <(
  ls -t "${BACKUP_DIR}"/backup_*.sql.gz.gpg 2>/dev/null | tail -n +15
)
if [ "${#OLD_FILES[@]}" -gt 0 ]; then
  echo "Removing ${#OLD_FILES[@]} old backup(s)"
  rm -- "${OLD_FILES[@]}"
fi

echo "Backup complete."
