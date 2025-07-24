# Multi-stage build for optimized production image
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DJANGO_SETTINGS_MODULE=brownie_car_rent.settings.production

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    build-essential \
    libpq-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip and install wheel for faster installs
RUN pip install --no-cache-dir --upgrade pip wheel

# Create app user early
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Copy and install Python dependencies first for better caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=app:app . /app/

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chown -R app:app /app

# Switch to app user
USER app

# Collect static files (will be overridden in docker-compose for development)
RUN python manage.py collectstatic --noinput --clear || true

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=10)" || exit 1

# Expose port
EXPOSE 8000

# Run the application with better gunicorn configuration
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "30", \
     "--keep-alive", "5", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "brownie_car_rent.wsgi:application"]
