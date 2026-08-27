#!/bin/bash
# ============================================================
# ShulePlusERP - Backup ya Kila Siku
# Weka: /home/ubuntu/shuleplus_erp/deploy/backup.sh
# Fanya iwe executable: chmod +x backup.sh
# Jaribu kwa mkono kwanza: ./backup.sh
# ============================================================

set -e  # simama ukikutana na error yoyote

# --- MAREKEBISHO YA LAZIMA KABLA YA KUTUMIA ---
DB_NAME="shulepluserp_db"
DB_USER="shule_user"
MEDIA_DIR="/home/ubuntu/shuleplus_erp/media"
BACKUP_DIR="/home/ubuntu/backups"
KEEP_DAYS=7
# ------------------------------------------------

DATE=$(date +%Y-%m-%d_%H-%M)
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Inaanza backup..."

# 1. Database (PostgreSQL)
pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# 2. Media files (risiti, picha, PDF zilizohifadhiwa)
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" -C "$(dirname "$MEDIA_DIR")" "$(basename "$MEDIA_DIR")"

echo "[$(date)] Backup imekamilika: db_$DATE.sql.gz na media_$DATE.tar.gz"

# 3. Futa backups za zamani (zaidi ya siku $KEEP_DAYS)
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +$KEEP_DAYS -delete
find "$BACKUP_DIR" -name "media_*.tar.gz" -mtime +$KEEP_DAYS -delete

echo "[$(date)] Backups za zamani (zaidi ya siku $KEEP_DAYS) zimefutwa."

# ============================================================
# HIARI: Tuma backup nje ya server (bora zaidi - server ikiharibika
# kabisa, backup ya ndani ya server hiyo hiyo haitasaidia).
# Chagua MOJA kati ya hizi (ondoa # kwenye uliyoichagua):
# ============================================================

# A) Oracle Object Storage (kama unatumia Oracle Cloud - free tier ~20GB)
# oci os object put --bucket-name shuleplus-backups \
#   --file "$BACKUP_DIR/db_$DATE.sql.gz" --name "db_$DATE.sql.gz"

# B) Rclone kwenda Google Drive (bure, rahisi kuweka - `rclone config` kwanza)
# rclone copy "$BACKUP_DIR/db_$DATE.sql.gz" gdrive:ShulePlusBackups/
# rclone copy "$BACKUP_DIR/media_$DATE.tar.gz" gdrive:ShulePlusBackups/

echo "[$(date)] Backup process imekamilika kikamilifu."
