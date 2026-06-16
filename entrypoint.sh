#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Celebobo Application Stack Startup              ║${NC}"
echo -e "${BLUE}║              Python 3.12+ | Django 5.2                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Python version check
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python Version: $PYTHON_VERSION${NC}"

# Database migrations
echo -e "\n${BLUE}[1/5] Running Database Migrations...${NC}"
python manage.py migrate --noinput

# Collect static files
echo -e "${BLUE}[2/5] Collecting Static Files...${NC}"
python manage.py collectstatic --noinput --clear 2>/dev/null || echo "⚠ Static files collection skipped"

# Create logs directory
mkdir -p /app/logs

# Check environment and start services
MODE=${APP_MODE:-dev}
echo -e "${BLUE}[3/5] Detected Mode: ${YELLOW}$MODE${NC}"

if [ "$MODE" = "dev" ]; then
    # ====== DEVELOPMENT MODE ======
    # All services in parallel in one container
    echo -e "\n${GREEN}Starting Development Mode - All Services${NC}"
    echo -e "${YELLOW}Available on: http://localhost:8000${NC}\n"
    
    # Terminal 1: Redis Server
    echo -e "${BLUE}[4/5] Starting Redis Server...${NC}"
    echo "   Port: 6379"
    redis-server --loglevel notice --dir /tmp &
    REDIS_PID=$!
    sleep 2
    
    # Verify Redis
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Redis is running (PID: $REDIS_PID)${NC}"
    else
        echo -e "${RED}   ✗ Redis failed to start${NC}"
        exit 1
    fi
    
    # Terminal 2: Celery Worker
    echo -e "${BLUE}Starting Celery Worker...${NC}"
    echo "   Concurrency: 4 workers"
    celery -A shopproject worker -l info --concurrency=4 &
    CELERY_PID=$!
    sleep 3
    echo -e "${GREEN}   ✓ Celery Worker is running (PID: $CELERY_PID)${NC}"
    
    # Terminal 3: Celery Beat (Scheduler)
    echo -e "${BLUE}Starting Celery Beat...${NC}"
    celery -A shopproject beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler &
    BEAT_PID=$!
    sleep 2
    echo -e "${GREEN}   ✓ Celery Beat is running (PID: $BEAT_PID)${NC}"
    
    # Terminal 4: Django Development Server
    echo -e "${BLUE}[5/5] Starting Django Development Server...${NC}"
    echo "   Host: 0.0.0.0:8000"
    echo "   Workers: 1 (dev mode)"
    python manage.py runserver 0.0.0.0:8000 &
    DJANGO_PID=$!
    sleep 2
    echo -e "${GREEN}   ✓ Django is running (PID: $DJANGO_PID)${NC}"
    
    echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         All Services Started Successfully! 🎉             ║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║ Django:     http://localhost:8000                          ║${NC}"
    echo -e "${GREEN}║ Redis:      redis://localhost:6379                         ║${NC}"
    echo -e "${GREEN}║ Celery:     Monitoring with celery -A shopproject events   ║${NC}"
    echo -e "${GREEN}║ Logs:       /app/logs/                                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    
    # Trap signals for graceful shutdown
    trap "echo -e '${YELLOW}Shutting down services...${NC}'; kill $DJANGO_PID $CELERY_PID $BEAT_PID $REDIS_PID 2>/dev/null; exit 0" SIGTERM SIGINT
    
    # Keep container alive
    wait

elif [ "$MODE" = "prod" ]; then
    # ====== PRODUCTION MODE ======
    # Use Gunicorn with Supervisor for process management
    echo -e "\n${GREEN}Starting Production Mode - Gunicorn + Supervisor${NC}\n"
    
    # Create supervisor config
    cat > /etc/supervisor/conf.d/celebobo.conf << 'SUPERVISOR'
[program:gunicorn]
command=gunicorn --bind 0.0.0.0:8000 --workers=4 --threads=2 --timeout=300 --access-logfile /app/logs/gunicorn_access.log --error-logfile /app/logs/gunicorn_error.log shopproject.wsgi:application
directory=/app
autostart=true
autorestart=true
stopasgroup=true
stdout_logfile=/app/logs/gunicorn.log
stdout_logfile_maxbytes=1MB
stdout_logfile_backups=5

[program:celery_worker]
command=celery -A shopproject worker -l info --concurrency=4
directory=/app
autostart=true
autorestart=true
stopasgroup=true
stdout_logfile=/app/logs/celery_worker.log
stdout_logfile_maxbytes=1MB
stdout_logfile_backups=5

[program:celery_beat]
command=celery -A shopproject beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/app
autostart=true
autorestart=true
stopasgroup=true
stdout_logfile=/app/logs/celery_beat.log
stdout_logfile_maxbytes=1MB
stdout_logfile_backups=5

[group:celebobo]
programs=gunicorn,celery_worker,celery_beat
SUPERVISOR
    
    echo -e "${BLUE}✓ Supervisor configuration created${NC}"
    echo -e "${BLUE}Starting Supervisor with 3 processes: Gunicorn, Celery Worker, Celery Beat${NC}\n"
    
    exec supervisord -c /etc/supervisor/supervisord.conf

elif [ "$MODE" = "worker" ]; then
    # ====== WORKER ONLY MODE ======
    # Horizontal scaling: just Celery workers (for scaling)
    echo -e "\n${GREEN}Starting Worker Mode - Celery Only${NC}"
    echo -e "${YELLOW}This container runs only Celery workers for horizontal scaling${NC}\n"
    
    echo -e "${BLUE}[4/5] Starting Celery Worker...${NC}"
    echo "   Concurrency: 4 workers"
    echo "   Connect to broker: $CELERY_BROKER_URL"
    
    exec celery -A shopproject worker -l info --concurrency=4

elif [ "$MODE" = "scheduler" ]; then
    # ====== SCHEDULER ONLY MODE ======
    # Single scheduler instance (Celery Beat)
    echo -e "\n${GREEN}Starting Scheduler Mode - Celery Beat Only${NC}"
    echo -e "${YELLOW}This container runs only Celery Beat (scheduler) - run only ONE instance${NC}\n"
    
    echo -e "${BLUE}[4/5] Starting Celery Beat...${NC}"
    echo "   Scheduler: DatabaseScheduler"
    echo "   Connect to broker: $CELERY_BROKER_URL"
    
    exec celery -A shopproject beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

elif [ "$MODE" = "web" ]; then
    # ====== WEB ONLY MODE ======
    # Just the Django web server (for horizontal scaling)
    echo -e "\n${GREEN}Starting Web Mode - Django Only${NC}"
    echo -e "${YELLOW}This container runs only Django web server for horizontal scaling${NC}\n"
    
    echo -e "${BLUE}[4/5] Starting Gunicorn...${NC}"
    echo "   Host: 0.0.0.0:8000"
    echo "   Workers: 4"
    echo "   Threads: 2 per worker"
    
    exec gunicorn --bind 0.0.0.0:8000 \
        --workers=4 \
        --threads=2 \
        --timeout=300 \
        --access-logfile - \
        --error-logfile - \
        shopproject.wsgi:application

else
    # ====== DEFAULT: DJANGO ONLY ======
    echo -e "\n${GREEN}Starting Default Mode - Django Development Server${NC}"
    echo -e "${YELLOW}Available on: http://localhost:8000${NC}\n"
    
    echo -e "${BLUE}[4/5] Starting Django Development Server...${NC}"
    python manage.py runserver 0.0.0.0:8000
fi
