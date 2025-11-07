#!/bin/bash
# Generate Random Password
# Generates a secure random password

LENGTH=${1:-16}

if [ "$LENGTH" -lt 8 ]; then
    echo "Password length must be at least 8 characters"
    exit 1
fi

PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-$LENGTH)
echo "$PASSWORD"
echo "$PASSWORD" | pbcopy 2>/dev/null && echo "✓ Copied to clipboard"

