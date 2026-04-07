# ============================================================
# Custom Redis 7 image for BioChemAI
# Includes: password auth, persistence (AOF + RDB), memory policy
# ============================================================
FROM redis:7-alpine

LABEL maintainer="BioChemAI Platform" \
      description="Redis 7 with BioChemAI persistence and security configuration"

# Install bash for the entrypoint wrapper
RUN apk add --no-cache bash

# Copy custom Redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# Copy entrypoint wrapper that substitutes REDIS_PASSWORD at runtime
COPY redis-entrypoint.sh /usr/local/bin/redis-entrypoint.sh
RUN chmod +x /usr/local/bin/redis-entrypoint.sh

# Persist data written by Redis
VOLUME ["/data"]

EXPOSE 6379

# The entrypoint script replaces the password placeholder and launches Redis
ENTRYPOINT ["/usr/local/bin/redis-entrypoint.sh"]
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
