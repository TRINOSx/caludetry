# ═══════════════════════════════════════════════════════════
# VOC Mesh Platform — Root Dockerfile (DO detection fallback)
# ═══════════════════════════════════════════════════════════
#
# The actual deployment uses .do/app.yaml which points to
# individual Dockerfiles per service. This root Dockerfile
# exists so DO App Platform detects a deployable component.
# ═══════════════════════════════════════════════════════════

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY voc-mesh-platform/apps/api/pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY voc-mesh-platform/apps/api/app ./app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
