version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: shopproject
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache & Message Broker
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Django Application (Dev Mode)
  app:
    build: .
    environment:
      DEBUG: "True"
      APP_MODE: dev
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/shopproject
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: postgresql://postgres:postgres@postgres:5432/shopproject
      SECRET_KEY: dev-secret-key-change-in-production
      ALLOWED_HOSTS: localhost,127.0.0.1,app
    ports:
      - "8000:8000"  # Django
      - "6379:6379"  # Redis (from container)
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - .:/app
      - /app/__pycache__
    command: /app/entrypoint.sh
    stdin_open: true
    tty: true

volumes:
  postgres_data:
  redis_data:
