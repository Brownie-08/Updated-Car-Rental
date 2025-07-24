# Production Deployment Guide

This guide provides instructions for deploying the Car Rental System to production.

## Prerequisites

- Python 3.8+
- MySQL or PostgreSQL database
- Redis (for caching)
- Web server (Nginx/Apache)
- SSL certificate

## Environment Setup

### 1. Create Production Environment Variables

Copy `.env.example` to `.env` and configure production values:

```bash
# Django Environment Configuration
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
DJANGO_ENVIRONMENT=production

# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=your_production_db
DB_USER=your_db_user
DB_PASSWORD=your_secure_db_password
DB_HOST=your_db_host
DB_PORT=3306

# Allowed Hosts (your domain)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Brownie Car Rental <noreply@yourdomain.com>

# Site Configuration
SITE_URL=https://yourdomain.com
SITE_NAME=Brownie Car Rental

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Redis Configuration
REDIS_URL=redis://127.0.0.1:6379/1

# Admin Configuration
ADMIN_URL=secure-admin-url/

# Production Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Migration

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

## Security Checklist

### ✅ Environment Variables
- [ ] SECRET_KEY is set to a strong, unique value
- [ ] DEBUG is set to False
- [ ] ALLOWED_HOSTS is configured correctly
- [ ] Database credentials are secure
- [ ] Email credentials are secure

### ✅ HTTPS Configuration
- [ ] SSL certificate is installed
- [ ] SECURE_SSL_REDIRECT is True
- [ ] SECURE_HSTS_* settings are configured
- [ ] Cookie security settings are enabled

### ✅ Database Security
- [ ] Database user has minimal required permissions
- [ ] Database is not accessible from outside
- [ ] Regular backups are configured

### ✅ Server Security
- [ ] Server is updated with latest security patches
- [ ] Firewall is configured
- [ ] Only necessary ports are open
- [ ] SSH key authentication is enabled

## Performance Optimization

### 1. Static Files
Configure your web server to serve static files directly:

```nginx
# Nginx configuration example
location /static/ {
    alias /path/to/your/staticfiles/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location /media/ {
    alias /path/to/your/media/;
    expires 1y;
    add_header Cache-Control "public";
}
```

### 2. Database Optimization
- Enable query caching
- Create appropriate indexes
- Regular database maintenance

### 3. Redis Caching
Ensure Redis is running and configured for session storage and caching.

## Monitoring and Logging

### 1. Log Files
Monitor these log files:
- `/path/to/project/logs/django.log`
- `/path/to/project/logs/django_errors.log`

### 2. Error Tracking
Consider integrating with services like:
- Sentry
- Rollbar
- Bugsnag

### 3. Performance Monitoring
- New Relic
- DataDog
- Application Performance Monitoring (APM)

## Backup Strategy

### 1. Database Backups
```bash
# Create daily backup script
#!/bin/bash
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > backup_$(date +%Y%m%d).sql
```

### 2. File Backups
- Media files
- Static files
- Configuration files

### 3. Automated Backups
Set up automated backups using cron jobs or cloud services.

## Deployment Steps

### 1. Using systemd (Recommended)

Create systemd service file:

```ini
# /etc/systemd/system/car-rental.service
[Unit]
Description=Car Rental System
After=network.target

[Service]
Type=exec
User=your-user
Group=your-group
WorkingDirectory=/path/to/your/project
Environment=DJANGO_ENVIRONMENT=production
ExecStart=/path/to/your/venv/bin/python manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable car-rental.service
sudo systemctl start car-rental.service
```

### 2. Using Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn brownie_car_rent.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### 3. Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/your/cert.crt;
    ssl_certificate_key /path/to/your/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/your/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

## Post-Deployment

### 1. Health Checks
- [ ] Application is accessible
- [ ] Database connections work
- [ ] Email functionality works
- [ ] Static files are served correctly
- [ ] HTTPS is working
- [ ] Admin panel is accessible

### 2. Testing
- [ ] Run functional tests
- [ ] Test user registration/login
- [ ] Test car booking functionality
- [ ] Test email notifications

### 3. Monitoring Setup
- [ ] Set up log monitoring
- [ ] Configure alerts
- [ ] Set up performance monitoring

## Maintenance

### Regular Tasks
- Monitor log files for errors
- Check system resources
- Update dependencies
- Perform database maintenance
- Review security logs

### Updates
- Test updates in staging environment first
- Backup before updates
- Have rollback plan ready
- Monitor after updates

## Troubleshooting

### Common Issues

1. **Static files not loading**
   - Check `STATIC_ROOT` and `STATIC_URL` settings
   - Run `python manage.py collectstatic`
   - Verify web server configuration

2. **Database connection errors**
   - Check database credentials
   - Verify database server is running
   - Check network connectivity

3. **Email not sending**
   - Verify email settings
   - Check SMTP server configuration
   - Review email logs

4. **Permission errors**
   - Check file permissions
   - Verify user/group settings
   - Check directory ownership

For additional support, check the application logs and error templates created in the system.
