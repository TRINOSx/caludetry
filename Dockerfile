# ═══════════════════════════════════════════════════════════
# VOC Mesh Platform — Root Dockerfile
# ═══════════════════════════════════════════════════════════
#
# This Dockerfile exists so DigitalOcean App Platform can
# detect the repo as deployable. The actual services are
# deployed via .do/app.yaml which points to individual
# Dockerfiles in each service directory.
#
# For local development, use docker-compose:
#   cd voc-mesh-platform && docker compose up -d
#
# For DigitalOcean App Platform:
#   Connect repo → DO auto-detects .do/app.yaml
# ═══════════════════════════════════════════════════════════

FROM python:3.12-slim

WORKDIR /app

COPY voc-mesh-platform/apps/api/pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY voc-mesh-platform/apps/api/app ./app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
