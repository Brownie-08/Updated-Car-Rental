# 🚗 Car Rental System

[![Django](https://img.shields.io/badge/Django-4.2.23-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive, production-ready car rental management system built with Django, featuring modern architecture, payment processing, real-time chat, and containerized deployment.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🚀 Core Functionality
- **Vehicle Management**: Complete car inventory with categories, pricing, and availability
- **Booking System**: Advanced reservation system with calendar integration
- **Customer Management**: User profiles, booking history, and preferences
- **Order Processing**: Full rental workflow from booking to return
- **Payment Integration**: Stripe payment processing with webhook support
- **PDF Receipts**: Automated invoice and receipt generation

### 💰 Payment & Billing
- **Multiple Payment Methods**: Credit cards, PayPal integration
- **Secure Processing**: PCI-compliant payment handling
- **Pay Later Options**: Deferred payment for corporate clients
- **Automated Invoicing**: PDF receipt generation and email delivery
- **Transaction Tracking**: Complete payment history and reporting

### 💬 Communication
- **Real-time Chat**: WebSocket-powered customer support
- **AI Chat Bot**: Automated responses for common queries
- **Email Notifications**: Booking confirmations and reminders
- **Admin Messaging**: Internal communication system

### 🔐 Security & Authentication
- **Custom User System**: Extended Django user model
- **Role-based Access**: Customer, staff, and admin permissions
- **HTTPS Enforcement**: SSL/TLS security in production
- **Content Security Policy**: XSS protection headers
- **Session Management**: Secure authentication handling

### 📊 Admin & Analytics
- **Django Admin**: Enhanced administrative interface
- **Dashboard**: Real-time booking and revenue analytics
- **Reporting**: Comprehensive business intelligence
- **Audit Logs**: Complete activity tracking

### 🔧 Technical Features
- **REST API**: Complete API with OpenAPI documentation
- **Background Tasks**: Celery for async processing
- **Caching**: Redis for performance optimization
- **WebSocket Support**: Real-time notifications
- **Docker Ready**: Complete containerization
- **Multi-environment**: Development, staging, production configs

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django App    │    │   Database      │
│   (Templates/   │◄──►│   (Web Server)  │◄──►│   (PostgreSQL)  │
│    Static)      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Cache   │◄──►│   Celery        │    │   External APIs │
│   (Session/     │    │   (Background   │◄──►│   (Stripe,      │
│    Queue)       │    │    Tasks)       │    │    PayPal)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack
- **Backend**: Django 4.2.23, Django REST Framework
- **Database**: PostgreSQL 15
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery with Redis broker
- **Payments**: Stripe, PayPal
- **WebSockets**: Django Channels
- **Containerization**: Docker & Docker Compose
- **Web Server**: Gunicorn (production)
- **Static Files**: WhiteNoise

## ⚡ Quick Start

### Prerequisites
- Docker Desktop installed
- Git
- 8GB+ RAM recommended

### 1-Minute Setup
```bash
# Clone the repository
git clone https://github.com/Brownie-08/Updated-Car-Rental.git
cd Updated-Car-Rental

# Start all services
docker-compose up -d

# Access the application
open http://localhost:8000
```

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123`
- Admin Panel: http://localhost:8000/admin

## 🛠️ Installation

### Method 1: Docker (Recommended)

1. **Clone and Setup**
   ```bash
   git clone https://github.com/yourusername/car-rental-system.git
   cd car-rental-system/brownie_car_rent
   ```

2. **Environment Configuration**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit configuration (optional for development)
   nano .env
   ```

3. **Build and Start Services**
   ```bash
   # Build containers
   docker-compose build
   
   # Start all services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   ```

4. **Initialize Database**
   ```bash
   # Run migrations
   docker-compose exec web python manage.py migrate
   
   # Create superuser
   docker-compose exec web python manage.py createsuperuser
   
   # Load sample data (optional)
   docker-compose exec web python manage.py loaddata fixtures/sample_data.json
   ```

### Method 2: Local Development

1. **System Requirements**
   ```bash
   # Python 3.9+
   python --version
   
   # PostgreSQL 15+
   psql --version
   
   # Redis Server
   redis-server --version
   ```

2. **Python Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb car_rental_db
   
   # Run migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   ```

4. **Start Services**
   ```bash
   # Terminal 1: Django server
   python manage.py runserver
   
   # Terminal 2: Celery worker
   celery -A brownie_car_rent worker -l info
   
   # Terminal 3: Celery beat (scheduled tasks)
   celery -A brownie_car_rent beat -l info
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=car_rental_db
DB_USER=car_rental_user
DB_PASSWORD=car_rental_password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Payment Gateways
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_MODE=sandbox  # or 'live' for production

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# File Storage (Production)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_STORAGE_BUCKET_NAME=your_bucket_name
```

### Docker Services

| Service | Port | Description |
|---------|------|-------------|
| Web Application | 8000 | Django development server |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache and message broker |
| Celery Worker | - | Background task processor |
| Celery Beat | - | Scheduled task scheduler |

### Service Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart web

# View service logs
docker-compose logs -f web

# Execute commands in containers
docker-compose exec web python manage.py shell
docker-compose exec db psql -U car_rental_user -d car_rental_db

# Scale services
docker-compose up -d --scale celery=3
```

## 📚 API Documentation

### REST API Endpoints

The system provides a comprehensive REST API for integration:

- **Interactive Documentation**: http://localhost:8000/api/docs/
- **OpenAPI Schema**: http://localhost:8000/api/schema/
- **API Root**: http://localhost:8000/api/v1/

### Key Endpoints

```
Authentication:
POST   /api/v1/auth/login/          # User login
POST   /api/v1/auth/logout/         # User logout
POST   /api/v1/auth/register/       # User registration

Cars:
GET    /api/v1/cars/               # List all cars
GET    /api/v1/cars/{id}/          # Get car details
POST   /api/v1/cars/               # Create car (admin)

Bookings:
GET    /api/v1/bookings/           # List user bookings
POST   /api/v1/bookings/           # Create new booking
GET    /api/v1/bookings/{id}/      # Get booking details

Payments:
POST   /api/v1/payments/stripe/    # Process Stripe payment
POST   /api/v1/payments/paypal/    # Process PayPal payment
GET    /api/v1/payments/{id}/      # Get payment status
```

### Authentication

The API uses Token-based authentication:

```python
# Request headers
Authorization: Token your_api_token_here
Content-Type: application/json
```

### Example API Usage

```python
import requests

# Login to get token
response = requests.post('http://localhost:8000/api/v1/auth/login/', {
    'username': 'your_username',
    'password': 'your_password'
})
token = response.json()['token']

# Use token for authenticated requests
headers = {'Authorization': f'Token {token}'}
cars = requests.get('http://localhost:8000/api/v1/cars/', headers=headers)
```

## 🧪 Testing

### Running Tests

```bash
# Docker environment
docker-compose exec web python manage.py test

# Local environment
python manage.py test

# Run specific test modules
python manage.py test system.tests.test_payment_integration
python manage.py test system.tests.test_booking_system

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Test Categories

- **Unit Tests**: Model and utility function tests
- **Integration Tests**: API endpoint testing
- **Payment Tests**: Stripe and PayPal integration tests
- **Email Tests**: Notification system tests
- **Chat Tests**: WebSocket and bot functionality tests

### Testing Payment Integration

```python
# Test Stripe payments
python manage.py test system.tests.test_payment_integration.StripePaymentTest

# Test PayPal integration
python manage.py test system.tests.test_payment_integration.PayPalPaymentTest
```

## 🚀 Deployment

### Production Deployment with Docker

1. **Prepare Production Environment**
   ```bash
   # Create production environment file
   cp .env.example .env.prod
   
   # Update production settings
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

2. **Use Production Docker Compose**
   ```bash
   # Build production images
   docker-compose -f docker-compose.prod.yml build
   
   # Start production services
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **SSL/HTTPS Setup**
   ```bash
   # Using Let's Encrypt with Nginx
   docker-compose exec nginx certbot --nginx -d yourdomain.com
   ```

### AWS Deployment

1. **EC2 Instance Setup**
   ```bash
   # Launch EC2 instance (t3.medium recommended)
   # Install Docker and Docker Compose
   sudo yum update -y
   sudo yum install -y docker
   sudo systemctl start docker
   sudo usermod -a -G docker ec2-user
   ```

2. **RDS Database**
   ```bash
   # Create PostgreSQL RDS instance
   # Update connection settings in .env.prod
   DB_HOST=your-rds-endpoint.amazonaws.com
   ```

3. **ElastiCache Redis**
   ```bash
   # Create Redis cluster
   # Update Redis settings
   REDIS_URL=redis://your-elasticache-endpoint:6379/0
   ```

### Environment-Specific Settings

```python
# brownie_car_rent/settings/production.py
import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Static files (AWS S3)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.StaticS3Boto3Storage'
```

## 🔧 Troubleshooting

### Common Issues

1. **Container Won't Start**
   ```bash
   # Check logs
   docker-compose logs web
   
   # Check ports
   netstat -an | grep 8000
   
   # Reset containers
   docker-compose down -v
   docker-compose up -d
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   docker-compose exec web python manage.py dbshell
   
   # Check database status
   docker-compose exec db pg_isready -U car_rental_user
   ```

3. **Payment Issues**
   ```bash
   # Verify Stripe webhook
   stripe listen --forward-to localhost:8000/payments/stripe/webhook/
   
   # Test payment processing
   docker-compose exec web python manage.py test system.tests.test_payment_integration
   ```

4. **Static Files Not Loading**
   ```bash
   # Collect static files
   docker-compose exec web python manage.py collectstatic --noinput
   
   # Check static files settings
   docker-compose exec web python manage.py shell -c "from django.conf import settings; print(settings.STATIC_URL)"
   ```

### Performance Optimization

```bash
# Enable Redis caching
CACHE_BACKEND = 'redis://redis:6379/1'

# Database query optimization
DEBUG_TOOLBAR = True  # Development only

# Gunicorn worker tuning (production)
workers = multiprocessing.cpu_count() * 2 + 1
```

## 📄 Project Structure

```
car-rental-system/
├── brownie_car_rent/           # Main Django project
│   ├── account/                # User authentication app
│   ├── api/                    # REST API endpoints
│   ├── system/                 # Core business logic
│   │   ├── management/         # Django management commands
│   │   ├── migrations/         # Database migrations
│   │   ├── templates/          # HTML templates
│   │   ├── static/             # CSS, JS, images
│   │   ├── models.py           # Data models
│   │   ├── views.py            # View controllers
│   │   ├── forms.py            # Django forms
│   │   ├── admin.py            # Admin interface
│   │   ├── urls.py             # URL routing
│   │   ├── payment_services.py # Payment processing
│   │   ├── email_utils.py      # Email functionality
│   │   └── bot_service.py      # Chatbot logic
│   ├── brownie_car_rent/       # Project settings
│   │   ├── settings/           # Environment-specific settings
│   │   │   ├── base.py         # Base configuration
│   │   │   ├── development.py  # Development settings
│   │   │   └── production.py   # Production settings
│   │   ├── urls.py             # Main URL configuration
│   │   ├── wsgi.py             # WSGI configuration
│   │   └── asgi.py             # ASGI configuration (WebSockets)
│   ├── templates/              # Global templates
│   ├── static/                 # Global static files
│   ├── media/                  # User uploaded files
│   ├── docker/                 # Docker configuration files
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Container definition
│   ├── docker-compose.yml      # Development services
│   ├── docker-compose.prod.yml # Production services
│   ├── manage.py               # Django management script
│   └── .env.example            # Environment template
├── docs/                       # Documentation
├── tests/                      # Additional test files
├── scripts/                    # Deployment scripts
├── README.md                   # This file
└── LICENSE                     # License file
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/car-rental-system.git
   cd car-rental-system
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Development Setup**
   ```bash
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Install pre-commit hooks
   pre-commit install
   ```

4. **Make Changes**
   - Write tests for new features
   - Follow PEP 8 style guidelines
   - Update documentation as needed

5. **Run Tests**
   ```bash
   # Run all tests
   python manage.py test
   
   # Run linting
   flake8 .
   black .
   ```

6. **Submit Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Ensure all tests pass

### Development Guidelines

- **Code Style**: Follow PEP 8, use Black formatter
- **Testing**: Maintain >90% test coverage
- **Documentation**: Update README and docstrings
- **Security**: Follow OWASP guidelines
- **Performance**: Profile and optimize critical paths

## 📊 Features Roadmap

### Current Version (v1.0)
- ✅ Basic car rental management
- ✅ Payment processing (Stripe, PayPal)
- ✅ Real-time chat system
- ✅ Email notifications
- ✅ Docker containerization
- ✅ REST API

### Upcoming Features (v1.1)
- 🔄 Mobile app (React Native)
- 🔄 Advanced reporting dashboard
- 🔄 Multi-location support
- 🔄 Fleet maintenance tracking
- 🔄 Customer loyalty program
- 🔄 SMS notifications

### Future Releases (v2.0)
- 📋 AI-powered pricing optimization
- 📋 IoT vehicle tracking
- 📋 Blockchain-based contracts
- 📋 Advanced analytics & ML
- 📋 Multi-tenant architecture

## 🔐 Security

### Security Features
- **HTTPS Enforcement**: All traffic encrypted
- **CSRF Protection**: Django built-in protection
- **SQL Injection Prevention**: ORM-based queries
- **XSS Protection**: Template auto-escaping
- **Authentication**: Secure session management
- **Input Validation**: Form and API validation

### Security Best Practices
```python
# Enable security middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
]

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
```

## 📞 Support

### Getting Help

- **Documentation**: Check this README and inline docs
- **Issues**: Open a GitHub issue for bugs
- **Discussions**: Use GitHub Discussions for questions
- **Email**: contact@yourcompany.com

### Commercial Support

For enterprise deployment, custom features, or priority support:
- 📧 Email: enterprise@yourcompany.com
- 🌐 Website: https://yourcompany.com/car-rental-support
- 📞 Phone: +1-800-CAR-RENT

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Your Company Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **Django**: The web framework for perfectionists with deadlines
- **Docker**: Containerization platform
- **PostgreSQL**: Advanced open source database
- **Redis**: In-memory data structure store
- **Stripe**: Payment processing platform
- **Bootstrap**: Frontend component library
- **Font Awesome**: Icon library

---

<div align="center">

**Built with ❤️ by [Your Company Name](https://yourcompany.com)**

[⭐ Star us on GitHub](https://github.com/Brownie-08/Updated-Car-Rental) • [🐛 Report Bug](https://github.com/Brownie-08/Updated-Car-Rental/issues) • [💡 Request Feature](https://github.com/Brownie-08/Updated-Car-Rental/discussions)

</div>
