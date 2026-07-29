# syntax=docker/dockerfile:1
# Production image for the Helvio88/babybuddy fork.
# Pushed to ghcr.io/helvio88/babybuddy by .github/workflows/docker-publish.yml

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=babybuddy.settings.base \
    PORT=8000

WORKDIR /app

# System deps for pillow / psycopg2-binary / mysql optional build leftovers
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        libjpeg62-turbo \
        libpq5 \
        zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Ensure data dirs exist; runtime may mount volumes over these
RUN mkdir -p /app/data /app/media \
    && chmod +x /app/docker/entrypoint.sh

EXPOSE 8000

# Healthcheck hits the login page (no auth required for GET /login/)
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/login/" >/dev/null || exit 1

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "babybuddy.wsgi:application", "--config", "etc/gunicorn.py"]
