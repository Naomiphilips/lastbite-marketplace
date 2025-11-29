#!/usr/bin/env bash
set -e

# Wait for Postgres to be ready
python - <<'PY'
import os, time, psycopg
for _ in range(60):
    try:
        psycopg.connect(
            host=os.environ.get("POSTGRES_HOST","db"),
            dbname=os.environ.get("POSTGRES_DB","lastbite"),
            user=os.environ.get("POSTGRES_USER","lastbite"),
            password=os.environ.get("POSTGRES_PASSWORD","lastbite"),
            connect_timeout=2,
        ).close()
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("Database never became ready.")
PY

# Run migrations & launch dev server
python manage.py migrate --noinput
python manage.py collectstatic --noinput || true
exec python manage.py runserver 0.0.0.0:8000
