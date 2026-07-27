# ──────────────────────────────────────────────────────────────────────────────
# OMNI Digital Twin — Backend Dockerfile
# Production-ready Python 3.12 slim image
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Metadata
LABEL maintainer="OMNI Digital Twin"
LABEL version="1.0.0"
LABEL description="OMNI Digital Twin FastAPI Backend"

# ── System dependencies ────────────────────────────────────────────────────────
# Required for pdfplumber (poppler), python-docx, and passlib (bcrypt)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ────────────────────────────────────────────────
# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy application source ────────────────────────────────────────────────────
COPY . .

# ── Create uploads directory ───────────────────────────────────────────────────
RUN mkdir -p /app/uploads

# ── Expose application port ────────────────────────────────────────────────────
# On Render, this is dynamically assigned via the PORT environment variable
EXPOSE 8000

# ── Runtime environment defaults (overridden by deployment env vars) ───────────
# Do NOT set secret values here — pass them at runtime via environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ── Health check ───────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request, os; port = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/health')" || exit 1

# ── Start Uvicorn ──────────────────────────────────────────────────────────────
# --host 0.0.0.0 required so the container is reachable from outside
# We use sh -c to allow environment variable expansion for PORT
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"
