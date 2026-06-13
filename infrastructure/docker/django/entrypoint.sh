#!/bin/sh
set -e

echo "Waiting for PostgreSQL on $POSTGRES_HOST:$POSTGRES_PORT..."
while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER";
do sleep 1
done
echo "POSTGRESSQL is ready"

# Database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Booting server
# Remplace by gunicorn later on
exec python manage.py runserver 0.0.0.0:8000
