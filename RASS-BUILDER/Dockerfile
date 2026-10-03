# ==============================================================================
# RASS-BUILDER: Multi-Stage Production Dockerfile
# Stage 1: Build modern frontend SPA bundle
# Stage 2: Hardened Python 3.12 runtime with unprivileged non-root user
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Frontend SPA Compilation
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install --ignore-scripts

COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Hardened Python Application Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PORT=8000 \
    HOST=0.0.0.0 \
    RASS_ENV=production \
    RASS_LOG_LEVEL=INFO \
    RASS_DB_PATH=/app/backend/data/rass_builder.db

# Install minimal system tools (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Install Python runtime dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend/ /app/backend/

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Create storage and upload directories with correct ownership
RUN mkdir -p /app/backend/data /app/uploads /app/backend/models/checkpoints && \
    chown -R appuser:appgroup /app/backend/data /app/uploads /app/backend/models

# Expose HTTP port
EXPOSE 8000

# Switch to unprivileged execution user
USER appuser

# Lightweight Docker Healthcheck using Stage 10 operational probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production ASGI server entrypoint
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]
