FROM python:3.12-slim

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

ENV DATA_DIR=/app/data
ENV IMAGES_DIR=/app/images
ENV CACHE=true
ENV HOST=0.0.0.0:3000
ENV WORKERS=1

EXPOSE 3000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/health', timeout=5)" || exit 1

# Labels
LABEL org.opencontainers.image.title="PlacePix" \
      org.opencontainers.image.description="Self-hosted placeholder image service" \
      org.opencontainers.image.version="${GIT_VERSION}" \
      org.opencontainers.image.source="https://github.com/riadvice/placepix" \
      org.opencontainers.image.licenses="MIT"

CMD ["sh", "-c", "python -m uvicorn src.main:app --host 0.0.0.0 --port 3000 --workers $WORKERS"]
