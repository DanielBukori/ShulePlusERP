#!/bin/bash
# ============================================================
# ShulePlusERP - Restore Backup (JARIBU HII KABLA HUJAITEGEMEA!)
# Matumizi: ./restore.sh db_2026-08-05_02-00.sql.gz media_2026-08-05_02-00.tar.gz
# ============================================================

set -euo pipefail

DB_NAME="${DB_NAME:-shulepluserp_db}"
DB_USER="${DB_USER:-shule_user}"
MEDIA_DIR="${MEDIA_DIR:-/home/ubuntu/shuleplus_erp/media}"
BACKUP_DIR="${BACKUP_DIR:-/home/ubuntu/backups}"

DB_BACKUP="${1:-}"
MEDIA_BACKUP="${2:-}"

if [ -z "$DB_BACKUP" ] || [ -z "$MEDIA_BACKUP" ]; then
    echo "Matumizi: ./restore.sh <jina_la_db_backup.sql.gz> <jina_la_media_backup.tar.gz>"
    exit 1
fi

if [[ "$(basename "$DB_BACKUP")" != "$DB_BACKUP" || "$DB_BACKUP" != db_*.sql.gz ]]; then
    echo "Jina la DB backup si sahihi."
    exit 1
fi

if [[ "$(basename "$MEDIA_BACKUP")" != "$MEDIA_BACKUP" || "$MEDIA_BACKUP" != media_*.tar.gz ]]; then
    echo "Jina la media backup si sahihi."
    exit 1
fi

if [[ ! -f "$BACKUP_DIR/$DB_BACKUP" || ! -f "$BACKUP_DIR/$MEDIA_BACKUP" ]]; then
    echo "Backup moja au zote hazipo ndani ya $BACKUP_DIR."
    exit 1
fi

echo "Onyo: HII ITAFUTA DATA YA SASA NA KUIBADILISHA NA BACKUP. Una uhakika? (Andika 'NDIYO' kuendelea)"
read -r confirmation
if [ "$confirmation" != "NDIYO" ]; then
    echo "Imesitishwa."
    exit 1
fi

echo "Inarudisha database..."
psql -v ON_ERROR_STOP=1 -U "$DB_USER" "$DB_NAME" <<SQL
DROP SCHEMA public CASCADE;
CREATE SCHEMA public AUTHORIZATION "$DB_USER";
GRANT ALL ON SCHEMA public TO "$DB_USER";
SQL
gunzip -c "$BACKUP_DIR/$DB_BACKUP" | psql -U "$DB_USER" "$DB_NAME"

echo "Inarudisha media files..."
tar -xzf "$BACKUP_DIR/$MEDIA_BACKUP" -C "$(dirname "$MEDIA_DIR")"

echo "Restore imekamilika. Angalia mfumo kuhakikisha kila kitu kiko sawa."
