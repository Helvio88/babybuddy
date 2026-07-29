#!/bin/sh
set -eu

if [ -z "${SECRET_KEY:-}" ]; then
  echo "ERROR: SECRET_KEY environment variable is required." >&2
  exit 1
fi

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-babybuddy.settings.base}"

# Apply migrations on every start so schema stays current with the image.
python manage.py migrate --noinput

# Create cache table used by Baby Buddy when missing (idempotent).
python manage.py createcachetable 2>/dev/null || true

exec "$@"
