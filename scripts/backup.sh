#!/bin/bash
# UCOS Safety: Emergency Backup Script
# Creates timestamped backup of entire project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_BASE_DIR="$(dirname "$PROJECT_ROOT")/containerx_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE_DIR/backup_$TIMESTAMP"

echo "🚨 Creating UCOS backup..."
echo "   Source: $PROJECT_ROOT"
echo "   Destination: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Copy project (exclude .git, __pycache__, .db files)
rsync -av \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.db-journal' \
    --exclude='*.db-wal' \
    --exclude='*.db-shm' \
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    "$PROJECT_ROOT/" "$BACKUP_DIR/"

# Create backup manifest
cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << EOF
UCOS ContainerX Backup Manifest
===============================
Backup Date: $(date)
Source: $PROJECT_ROOT
Backup Location: $BACKUP_DIR

Contents:
- Core UCOS services
- Tests (scenarios + physics)
- Configuration files
- Documentation

To restore:
1. Copy backup directory to desired location
2. Restore database from backup if needed
3. Run: python -m pytest tests/scenarios/ tests/ucos_physics/
EOF

echo "✅ Backup created: $BACKUP_DIR"
echo "   Manifest: $BACKUP_DIR/BACKUP_MANIFEST.txt"
du -sh "$BACKUP_DIR"

