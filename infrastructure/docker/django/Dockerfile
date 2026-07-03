# BASIC Image
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

# Container working dir
WORKDIR /app

# PostgreSQL system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
	gcc \
	libpq-dev \
	postgresql-client \
    gettext\
	&& rm -rf /var/lib/apt/lists*

# Docker cache optimization
COPY backend/requirements/ ./requirements
RUN pip install --no-cache-dir -r requirements/dev.txt

# Backend
COPY backend/ .

# Copy + exec starting script
COPY infrastructure/docker/django/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Django Port
EXPOSE 8000

# containeur booting script
ENTRYPOINT [ "/entrypoint.sh" ]
