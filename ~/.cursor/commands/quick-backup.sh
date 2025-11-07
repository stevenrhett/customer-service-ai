#!/bin/bash
# Quick Backup
# Creates a quick backup of current directory

BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
PARENT_DIR=$(dirname "$(pwd)")

echo "Creating backup: $BACKUP_NAME"
tar -czf "$PARENT_DIR/$BACKUP_NAME.tar.gz" \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.next' \
    --exclude='venv' \
    --exclude='.venv' \
    -C "$(pwd)" .

echo "✓ Backup created: $PARENT_DIR/$BACKUP_NAME.tar.gz"

