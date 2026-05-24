FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code (images/ is mounted at runtime, never copied)
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/

# Ensure the mount point exists
RUN mkdir -p /app/images /app/.cache

ENV IMAGES_DIR=/app/images
ENV CACHE=true
ENV HOST=0.0.0.0:3000

EXPOSE 3000

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000"]
