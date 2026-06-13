# Environment Variables

Configuration is read from a `.env` file via [`python-decouple`]. Copy
`.env.example` to `.env` and adjust values. `.env` is gitignored and must
never be committed.

```bash
cp .env.example .env
```

## Variables

### Django

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `False` | Debug mode (set `True` in dev only) |
| `SECRET_KEY` | — (required) | Django secret key |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | Settings module to load |

### Localization

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGUAGE_CODE` | `fr` | Default language |
| `TIME_ZONE` | `Europe/Paris` | Default timezone |

### PostgreSQL

The `POSTGRES_*` names are **shared** by the postgres image, the Compose
healthcheck, the Django entrypoint and Django settings — keep them consistent.

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `lamos_chocolate` | Database name |
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_HOST` | `postgres` | Host — `postgres` (service) in Docker, `localhost` on the host |
| `POSTGRES_PORT` | `5432` | Database port |

### Site & email

| Variable | Default | Description |
|----------|---------|-------------|
| `SITE_URL` | `http://localhost:8000` | Public base URL (emails, links) |
| `DEFAULT_FROM_EMAIL` | `noreply@lamos-chocolate.ch` | Default sender |
| `EMAIL_HOST` / `EMAIL_PORT` | `` / `587` | SMTP server |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | `` | SMTP credentials |
| `EMAIL_USE_TLS` | `True` | Use TLS for SMTP |

### Stripe

| Variable | Description |
|----------|-------------|
| `STRIPE_PUBLIC_KEY` | Publishable key (`pk_...`) |
| `STRIPE_SECRET_KEY` | Secret key (`sk_...`) |
| `STRIPE_WEBHOOK_SECRET` | Webhook signing secret (`whsec_...`) |

[`python-decouple`]: https://pypi.org/project/python-decouple/
