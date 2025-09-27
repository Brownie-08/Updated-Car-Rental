#!/bin/bash

# =============================================================================
# CAR RENTAL SYSTEM - QUICK SETUP SCRIPT
# =============================================================================
# This script helps you set up the Car Rental System quickly on Unix systems
# For Windows, use setup.ps1 instead

set -e  # Exit on any error

echo "🚗 Car Rental System - Quick Setup"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker Desktop first."
        echo "Visit: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    print_success "Docker is installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed."
        exit 1
    fi
    print_success "Docker Compose is installed"
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    print_success "Docker is running"
}

# Setup environment file
setup_environment() {
    print_info "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        print_success "Environment file created from template"
        print_warning "Remember to update .env with your actual configuration"
    else
        print_warning "Environment file already exists, skipping..."
    fi
}

# Build and start services
start_services() {
    print_info "Building Docker images..."
    docker-compose build
    print_success "Docker images built successfully"
    
    print_info "Starting services..."
    docker-compose up -d
    print_success "Services started successfully"
    
    # Wait for services to be healthy
    print_info "Waiting for services to be ready..."
    sleep 30
}

# Setup database
setup_database() {
    print_info "Setting up database..."
    
    # Run migrations
    docker-compose exec web python manage.py migrate
    print_success "Database migrations completed"
    
    # Create superuser (optional)
    echo ""
    read -p "Would you like to create a superuser account? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose exec web python manage.py createsuperuser
    else
        print_info "Skipping superuser creation. You can create one later with:"
        print_info "docker-compose exec web python manage.py createsuperuser"
    fi
}

# Show final information
show_completion_info() {
    echo ""
    echo "🎉 Setup Complete!"
    echo "=================="
    echo ""
    print_success "Car Rental System is now running!"
    echo ""
    echo "📋 Access Information:"
    echo "   🌐 Application: http://localhost:8000"
    echo "   👑 Admin Panel: http://localhost:8000/admin"
    echo "   📚 API Docs:    http://localhost:8000/api/docs/"
    echo ""
    echo "🐳 Docker Services:"
    echo "   🔍 View logs:     docker-compose logs -f"
    echo "   ⏹️  Stop services: docker-compose down"
    echo "   🔄 Restart:       docker-compose restart"
    echo ""
    echo "🛠️  Useful Commands:"
    echo "   📊 Service status: docker-compose ps"
    echo "   🐚 Django shell:   docker-compose exec web python manage.py shell"
    echo "   🗄️  Database shell: docker-compose exec db psql -U car_rental_user -d car_rental_db"
    echo ""
    print_warning "Don't forget to:"
    echo "   1. Update your .env file with real configuration"
    echo "   2. Add your Stripe keys for payment processing"
    echo "   3. Configure email settings for notifications"
    echo ""
}

# Main execution
main() {
    echo "Starting Car Rental System setup..."
    echo ""
    
    check_prerequisites
    setup_environment
    start_services
    setup_database
    show_completion_info
    
    print_success "Setup completed successfully! 🚀"
}

# Run main function
main "$@"
