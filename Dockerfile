# Multi-stage production image for Celebobo e-commerce platform
# Python 3.12 | Django 5.2 | Gunicorn | Celery | Redis
# Supports multiple deployment modes: dev, prod, worker, scheduler, web

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    redis-server \
    supervisor \
    curl \
    wget \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Verify Python version
RUN python --version

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Install production servers
RUN pip install gunicorn==21.2.0

# Create necessary directories
RUN mkdir -p /var/log/supervisor /app/logs

# Copy application code
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create non-root user for security (optional, commented for simplicity)
# RUN useradd -m -u 1000 celebobo && chown -R celebobo:celebobo /app
# USER celebobo

# Expose ports
EXPOSE 8000 6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default to development mode if not specified
ENV APP_MODE=prod
