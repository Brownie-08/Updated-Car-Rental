# Docker Setup Guide for Car Rental System

This guide will help you set up and run the Car Rental System using Docker for both development and production environments.

## Prerequisites

1. **Docker Desktop** - Download and install from [docker.com](https://www.docker.com/products/docker-desktop/)
2. **Docker Compose** - Included with Docker Desktop
3. **Git** - For version control

## Quick Start

### 1. Start Docker Desktop
Make sure Docker Desktop is running on your system.

### 2. Development Environment

```powershell
# Start development environment with hot-reload
docker-compose up --build

# Or use the management script
./docker-scripts.ps1 -Action dev
```

Your application will be available at:
- **Django App**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 3. Production Environment

```powershell
# Copy and configure production environment file
cp .env.prod.example .env.prod
# Edit .env.prod with your production values

# Start production environment
docker-compose -f docker-compose.prod.yml up -d --build

# Or use the management script
./docker-scripts.ps1 -Action prod
```

Production services:
- **Django App**: http://localhost (via Nginx)
- **Celery Flower**: http://localhost:5555
- **SSL/HTTPS**: https://localhost (configure certificates)

## Docker Architecture

### Services Overview

#### Development (`docker-compose.yml`)
- **web**: Django application (development server)
- **db**: PostgreSQL 15 database
- **redis**: Redis for caching and Celery
- **celery**: Celery worker for background tasks
- **celery-beat**: Celery scheduler

#### Production (`docker-compose.prod.yml`)
- **web**: Django application (Gunicorn WSGI server)
- **db**: PostgreSQL 15 database (no exposed ports)
- **redis**: Redis (no exposed ports)
- **nginx**: Reverse proxy and static file server
- **celery**: Celery worker
- **celery-beat**: Celery scheduler
- **flower**: Celery monitoring dashboard

### Volume Management

- **postgres_data**: Database persistence
- **static_volume**: Static files (CSS, JS, images)
- **media_volume**: User uploads
- **redis_data**: Redis persistence
- **logs_volume**: Application logs

## Environment Configuration

### Development (.env)
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=car_rental_db
DB_USER=car_rental_user
DB_PASSWORD=car_rental_password
DB_HOST=db
DB_PORT=5432
DEBUG=1
```

### Production (.env.prod)
Use `.env.prod.example` as a template and update:
- Database credentials
- Secret keys
- Email configuration
- Stripe payment keys
- Domain settings

## Docker Management Commands

### Using PowerShell Script

```powershell
# Development
./docker-scripts.ps1 -Action dev

# Production
./docker-scripts.ps1 -Action prod

# Build images
./docker-scripts.ps1 -Action build

# View logs
./docker-scripts.ps1 -Action logs -Service web

# Open shell
./docker-scripts.ps1 -Action shell -Service web

# Run tests
./docker-scripts.ps1 -Action test

# Database backup
./docker-scripts.ps1 -Action backup

# Clean up
./docker-scripts.ps1 -Action clean
```

### Manual Docker Commands

```bash
# Build and start development
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f web

# Execute commands in container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py test

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Database Operations

### Initial Setup
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Load sample data (if available)
docker-compose exec web python manage.py loaddata fixtures/sample_data.json
```

### Backup and Restore
```bash
# Create backup
docker-compose exec db pg_dump -U car_rental_user car_rental_db > backup.sql

# Restore backup
docker-compose exec db psql -U car_rental_user car_rental_db < backup.sql
```

## Troubleshooting

### Common Issues

1. **Docker Desktop not running**
   ```
   Error: Cannot connect to the Docker daemon
   ```
   **Solution**: Start Docker Desktop application

2. **Port already in use**
   ```
   Error: Port 8000 is already allocated
   ```
   **Solution**: Stop other services or change ports in docker-compose.yml

3. **Database connection error**
   ```
   Error: could not connect to server
   ```
   **Solution**: Wait for database to initialize (30-60 seconds on first run)

4. **Permission denied in container**
   ```
   Error: Permission denied
   ```
   **Solution**: Check file ownership and .dockerignore

### Build Optimization Tips

1. **Use .dockerignore** to exclude unnecessary files
2. **Layer caching** - requirements.txt is copied before application code
3. **Multi-stage builds** for smaller production images
4. **Health checks** ensure services are ready before dependent services start

### Development vs Production Differences

| Feature | Development | Production |
|---------|-------------|------------|
| Web Server | Django runserver | Gunicorn |
| Debug Mode | ON | OFF |
| Database Ports | Exposed | Internal only |
| SSL/HTTPS | Not configured | Nginx with SSL |
| Static Files | Django serves | Nginx serves |
| Logging | Console | Files + Console |
| Auto-reload | Yes | No |

## Performance Monitoring

### Production Monitoring
- **Flower**: Celery task monitoring at http://localhost:5555
- **Logs**: Check `/app/logs/` in containers
- **Health Checks**: Built-in Docker health checks

### Development Debugging
- **Django Debug Toolbar**: Available in development
- **Hot Reload**: Code changes automatically reload
- **Database Admin**: Access via Django admin

## Security Considerations

### Production Security
- Database and Redis not exposed to host
- SSL/HTTPS configuration via Nginx
- Secure environment variables
- Non-root user in containers
- Regular security updates

### Development Security
- Exposed ports for debugging
- Debug mode enabled
- Default credentials (change for production)

## Next Steps

1. **Start Docker Desktop**
2. **Run development environment**: `docker-compose up --build`
3. **Access your application**: http://localhost:8000
4. **Create admin user**: `docker-compose exec web python manage.py createsuperuser`
5. **Run tests**: `docker-compose exec web python manage.py test`

For production deployment, configure `.env.prod` and use `docker-compose.prod.yml`.

## Support

If you encounter issues:
1. Check Docker Desktop is running
2. Review logs: `docker-compose logs`
3. Verify environment configuration
4. Check port availability
5. Restart services: `docker-compose restart`

Happy Dockerizing! 🐳
