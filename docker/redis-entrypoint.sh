#!/usr/bin/env bash
# ============================================================
# Redis entrypoint: substitute REDIS_PASSWORD env var into
# the Redis config file before launching the server.
# ============================================================
set -euo pipefail

CONFIG_FILE="/usr/local/etc/redis/redis.conf"

if [ -z "${REDIS_PASSWORD:-}" ]; then
    echo "ERROR: REDIS_PASSWORD environment variable is not set." >&2
    exit 1
fi

# Replace the placeholder with the actual password
sed -i "s|REDIS_PASSWORD_PLACEHOLDER|${REDIS_PASSWORD}|g" "$CONFIG_FILE"

exec "$@"
