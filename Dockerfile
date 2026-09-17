# syntax=docker/dockerfile:1

# Port the app listens on inside the container (override at build or run time).
# Declared before the first FROM so every stage can opt into it.
ARG PORT=3000

FROM python:3.12-slim AS base

ARG GIT_VERSION=dev
ENV GIT_VERSION=${GIT_VERSION}
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies for OpenCV and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application code (images/ is mounted at runtime, never copied)
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/
COPY robots.txt ./
COPY sitemap/ ./sitemap/

# Ensure the mount point exists
RUN mkdir -p /app/images /app/.cache /app/data

# NOTE: runtime configuration (HOST, PORT, DATA_DIR, IMAGES_DIR, ...) is
# deliberately NOT set here. Real environment variables outrank env_file in
# pydantic-settings, so anything set in `base` leaks into the `test` stage and
# silently overrides .env.test - pointing tests at production paths and ports.
# Those values belong to the `production` stage alone.

FROM base AS test

# Install development/test dependencies and copy the test suite
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -e '.[dev]'

COPY tests/ ./tests/
COPY .env.test ./
COPY unit_tests.sh ./

ENV TESTING=1
ENV ENV_FILE=/app/.env.test

ENTRYPOINT ["./unit_tests.sh"]
CMD ["--fast"]

FROM base AS production

ARG PORT
ENV PORT=${PORT}
ENV HOST=0.0.0.0:${PORT}
ENV DATA_DIR=/app/data
ENV IMAGES_DIR=/app/images
ENV CACHE=true
ENV WORKERS=1

EXPOSE ${PORT}

# Healthcheck (reads PORT at runtime, so changing it needs no rebuild)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '3000') + '/health', timeout=5)" || exit 1

# Labels
LABEL org.opencontainers.image.title="PlacePix" \
      org.opencontainers.image.description="Self-hosted placeholder image service" \
      org.opencontainers.image.version="${GIT_VERSION}" \
      org.opencontainers.image.source="https://github.com/riadvice/placepix" \
      org.opencontainers.image.licenses="MIT"

CMD ["sh", "-c", "python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-3000} --workers ${WORKERS:-1}"]
