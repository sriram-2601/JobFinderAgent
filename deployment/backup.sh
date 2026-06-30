#!/bin/bash
# Backup script for SQLite database

DB_DIR="./data"
DB_FILE="$DB_DIR/jobfinder.db"
BACKUP_DIR="$DB_DIR/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/jobfinder_backup_$TIMESTAMP.db"

# Create backup directory if it does not exist
mkdir -p "$BACKUP_DIR"

if [ -f "$BACKUP_FILE" ]; then
    echo "Backup already exists for this timestamp."
    exit 1
fi

if [ -f "$BACKUP_FILE" ] || cp "$DB_FILE" "$BACKUP_FILE"; then
    echo "Database backup created successfully: $BACKUP_FILE"
    
    # Delete backups older than 14 days to conserve disk space on free tiers
    find "$BACKUP_DIR" -type f -name "jobfinder_backup_*.db" -mtime +14 -delete
    echo "Purged old backups (older than 14 days)."
else
    echo "Backup failed: Database file not found or write error."
    exit 1
fi
