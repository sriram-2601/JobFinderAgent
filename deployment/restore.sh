#!/bin/bash
# Database restoration script

BACKUP_DIR="./data/backups"
DB_FILE="./data/jobfinder.db"

if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup_filename>"
    echo "Available backups:"
    ls -l "$BACKUP_DIR"/jobfinder_backup_*.db 2>/dev/null || echo "No backups found."
    exit 1
fi

BACKUP_PATH="$BACKUP_DIR/$1"

if [ ! -f "$BACKUP_PATH" ]; then
    # Fallback to direct path check
    BACKUP_PATH="$1"
    if [ ! -f "$BACKUP_PATH" ]; then
        echo "Error: Backup file not found at $BACKUP_PATH"
        exit 1
    fi
fi

# Stop backend container if running
echo "Pausing jobfinder service..."
docker-compose stop backend

# Copy backup file over active database
echo "Restoring database..."
cp "$BACKUP_PATH" "$DB_FILE"
chmod 664 "$DB_FILE"

# Restart containers
echo "Restarting service..."
docker-compose start backend

echo "Database successfully restored from $BACKUP_PATH."
