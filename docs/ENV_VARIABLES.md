# Environment Variables Reference Guide

**Status:** Complete  
**Last Updated:** 2026-05-05  
**Scope:** Celebobo E-Commerce Platform v1.0

---

## Quick Start

```bash
# Copy the example file
cp .env.example .env

# Fill in your values
nano .env  # or your editor

# Verify (Docker will fail early if required vars are missing)
docker-compose up
```

---

## Variable Categories

### 1. Django Core Configuration

#### SECRET_KEY
- **Type:** String
- **Required:** YES
- **Default:** None
- **Description:** Django secret key for cryptographic operations
- **How to Generate:**
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- **Security:** Keep this private! Never commit to version control. Different value per environment.
- **Example:** `SECRET_KEY=django-insecure-abc123def456...`

#### DEBUG
- **Type:** Boolean (True/False)
- **Required:** YES
- **Default:** None
- **Description:** Enable Django debug mode
- **Value:** 
  - `True` = Development (verbose errors, debug toolbar)
  - `False` = Production (generic error pages)
- **Security:** MUST be False in production!
- **Example:** `DEBUG=False`

#### ALLOWED_HOSTS
- **Type:** String (comma-separated domains)
- **Required:** YES
- **Default:** None
- **Description:** Hosts that Django will serve
- **Format:** `domain.com,www.domain.com,*.domain.com`
- **Why:** Prevents host-header attacks
- **Example:** `ALLOWED_HOSTS=localhost,127.0.0.1,celebobo.com,www.celebobo.com`

#### APP_MODE
- **Type:** String
- **Required:** NO (default: dev)
- **Default:** `dev`
- **Description:** Deployment mode
- **Options:**
  - `dev` - All services in one container (local development)
  - `prod` - Gunicorn + Supervisor + Celery (single VPS)
  - `worker` - Celery worker only (horizontal scaling)
  - `scheduler` - Celery Beat only (one instance max)
  - `web` - Gunicorn only (microservice)
- **Example:** `APP_MODE=prod`

#### LOG_LEVEL
- **Type:** String
- **Required:** NO (default: INFO)
- **Default:** `INFO`
- **Options:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Description:** Logging verbosity level
- **Example:** `LOG_LEVEL=DEBUG`

---

### 2. Database Configuration

#### DATABASE_URL
- **Type:** String (PostgreSQL connection string)
- **Required:** YES
- **Default:** None
- **Format:** `postgresql://username:password@host:port/dbname`
- **Description:** PostgreSQL database connection
- **Security:** Use strong password, restrict IP access
- **Examples:**
  - Local: `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/shopproject`
  - Docker: `DATABASE_URL=postgresql://postgres:postgres@postgres:5432/shopproject`
  - AWS RDS: `DATABASE_URL=postgresql://user:pass@db.xyz.rds.amazonaws.com:5432/shopproject`

---

### 3. Cache & Message Broker (Redis)

#### REDIS_URL
- **Type:** String (Redis connection string)
- **Required:** YES
- **Default:** None
- **Format:** `redis://[:password]@host:port/db`
- **Description:** Redis connection for caching and Celery broker
- **Examples:**
  - Local: `REDIS_URL=redis://localhost:6379/0`
  - Docker: `REDIS_URL=redis://redis:6379/0`

#### CELERY_BROKER_URL
- **Type:** String
- **Required:** NO (defaults to REDIS_URL)
- **Default:** Uses REDIS_URL
- **Description:** URL for Celery task broker

---

### 4. AI Assistant (Gemini)

#### GEMINI_API_KEY
- **Type:** String (API key)
- **Required:** YES (if AI features enabled)
- **Description:** Google Gemini API key
- **Get it:** https://ai.google.dev

#### GEMINI_MODEL
- **Type:** String
- **Default:** `gemini-2.5-flash`
- **Options:** gemini-2.5-flash, gemini-pro, gemini-vision-pro

#### GEMINI_TIMEOUT
- **Type:** Integer (seconds)
- **Default:** `30`

#### GEMINI_CACHE_TIMEOUT
- **Type:** Integer (seconds)
- **Default:** `300` (5 minutes)

#### GEMINI_MAX_HISTORY
- **Type:** Integer
- **Default:** `6`
- **Description:** Max messages in conversation history

#### GEMINI_MAX_MESSAGE_LENGTH
- **Type:** Integer (characters)
- **Default:** `500`

#### GEMINI_MAX_TOKENS
- **Type:** Integer
- **Default:** `400`

#### GEMINI_TEMPERATURE
- **Type:** Float (0.0-1.0)
- **Default:** `0.7`
- **Description:** Randomness (0=deterministic, 1=creative)

#### GEMINI_TOP_P
- **Type:** Float (0.0-1.0)
- **Default:** `0.95`

---

### 5. File Storage (Cloudinary)

#### CLOUDINARY_CLOUD_NAME
- **Type:** String
- **Required:** YES (if using Cloudinary)
- **Get it:** https://cloudinary.com dashboard

#### CLOUDINARY_API_KEY
- **Type:** String
- **Required:** YES
- **Get it:** Cloudinary Settings → API Keys

#### CLOUDINARY_API_SECRET
- **Type:** String (SECRET)
- **Required:** YES
- **Security:** Keep secret!

---

### 6. Email Configuration

#### EMAIL_BACKEND
- **Type:** String
- **Default:** `django.core.mail.backends.console.EmailBackend`
- **Production:** `django.core.mail.backends.smtp.EmailBackend`

#### EMAIL_HOST
- **Type:** String
- **Examples:** smtp.gmail.com, smtp.sendgrid.net

#### EMAIL_PORT
- **Type:** Integer
- **Default:** `587` (TLS)

#### EMAIL_USE_TLS
- **Type:** Boolean
- **Default:** `True`

#### EMAIL_HOST_USER
- **Type:** String
- **Example:** your-email@gmail.com

#### EMAIL_HOST_PASSWORD
- **Type:** String (SECRET)
- **Gmail:** Use app-specific password

#### DEFAULT_FROM_EMAIL
- **Type:** String (email address)
- **Default:** `noreply@example.com`

#### SUPPORT_EMAIL
- **Type:** String (email address)

---

### 7. Product Analytics

#### PRODUCT_ANALYTICS_TOP_N
- **Type:** Integer
- **Default:** `15`
- **Description:** Number of top products to track

#### PRODUCT_ANALYTICS_EMAIL_RECIPIENTS
- **Type:** String (comma-separated)
- **Format:** `email1@domain.com,email2@domain.com`

#### PRODUCT_ANALYTICS_SEND_DAY
- **Type:** String
- **Default:** `monday`
- **Options:** monday, tuesday, wednesday, thursday, friday, saturday, sunday

#### PRODUCT_ANALYTICS_SEND_TIME
- **Type:** String (HH:MM)
- **Default:** `09:00`

#### PRODUCT_ANALYTICS_RETENTION_DAYS
- **Type:** Integer
- **Default:** `90`

---

### 8. Site Configuration

#### SITE_NAME
- **Type:** String
- **Default:** `Celebobo`

#### SITE_URL
- **Type:** String (URL)
- **Used:** Email templates

#### SUPPORT_PHONE
- **Type:** String
- **Used:** Error messages, templates

---

### 9. Celery Configuration

#### CELERY_TASK_TIME_LIMIT
- **Type:** Integer (seconds)
- **Default:** `600`

#### CELERY_TASK_SOFT_TIME_LIMIT
- **Type:** Integer (seconds)
- **Default:** `580`

#### CELERY_WORKER_CONCURRENCY
- **Type:** Integer
- **Default:** `4`
- **Calculation:** (CPU cores × 2) + 1 for CPU-bound, (CPU cores × 4) + 1 for I/O-bound

#### CELERY_TIMEZONE
- **Type:** String (timezone)
- **Default:** `UTC`

---

### 10. Security Headers

#### SECURE_SSL_REDIRECT
- **Type:** Boolean
- **Default:** `False`
- **Production:** `True`

#### SECURE_HSTS_SECONDS
- **Type:** Integer (seconds)
- **Default:** `31536000` (1 year)

#### CSRF_TRUSTED_ORIGINS
- **Type:** String (comma-separated URLs)
- **Format:** Full URLs with protocol

---

## Environment Setup Examples

### Local Development
```bash
DEBUG=True
APP_MODE=dev
SECRET_KEY=dev-key
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/shopproject
REDIS_URL=redis://redis:6379/0
```

### Production
```bash
DEBUG=False
APP_MODE=prod
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

---

## Security Best Practices

1. **Never commit .env**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use strong secrets**
3. **Different per environment**
4. **Rotate credentials regularly**
5. **Use environment variables for all secrets**

---

## Troubleshooting

### Missing Variable
- Add to .env and restart

### Database Connection Failed
- Check DATABASE_URL format and connectivity

### Redis Timeout
- Verify REDIS_URL and Redis is running

### Email Not Sending
- For Gmail: use app-specific password (not account password)
