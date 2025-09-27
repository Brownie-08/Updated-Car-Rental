# =============================================================================
# CAR RENTAL SYSTEM - QUICK SETUP SCRIPT (PowerShell)
# =============================================================================
# This script helps you set up the Car Rental System quickly on Windows
# For Unix systems, use setup.sh instead

param(
    [switch]$SkipSuperuser = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚗 Car Rental System - Quick Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Function to print colored output
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor White
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>$null
        if (-not $dockerVersion) {
            throw "Docker not found"
        }
        Write-Success "Docker is installed"
    }
    catch {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        Write-Host "Visit: https://www.docker.com/products/docker-desktop" -ForegroundColor Blue
        exit 1
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version 2>$null
        if (-not $composeVersion) {
            throw "Docker Compose not found"
        }
        Write-Success "Docker Compose is installed"
    }
    catch {
        Write-Error "Docker Compose is not installed."
        exit 1
    }
    
    # Check if Docker is running
    try {
        docker info 2>$null | Out-Null
        Write-Success "Docker is running"
    }
    catch {
        Write-Error "Docker is not running. Please start Docker Desktop."
        exit 1
    }
}

# Setup environment file
function Initialize-Environment {
    Write-Info "Setting up environment configuration..."
    
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Success "Environment file created from template"
        Write-Warning "Remember to update .env with your actual configuration"
    }
    else {
        Write-Warning "Environment file already exists, skipping..."
    }
}

# Build and start services
function Start-Services {
    Write-Info "Building Docker images..."
    try {
        docker-compose build
        Write-Success "Docker images built successfully"
    }
    catch {
        Write-Error "Failed to build Docker images"
        throw
    }
    
    Write-Info "Starting services..."
    try {
        docker-compose up -d
        Write-Success "Services started successfully"
    }
    catch {
        Write-Error "Failed to start services"
        throw
    }
    
    # Wait for services to be healthy
    Write-Info "Waiting for services to be ready..."
    Start-Sleep -Seconds 30
}

# Setup database
function Initialize-Database {
    Write-Info "Setting up database..."
    
    # Run migrations
    try {
        docker-compose exec web python manage.py migrate
        Write-Success "Database migrations completed"
    }
    catch {
        Write-Error "Failed to run database migrations"
        throw
    }
    
    # Create superuser (optional)
    if (-not $SkipSuperuser) {
        Write-Host ""
        $createSuperuser = Read-Host "Would you like to create a superuser account? (y/n)"
        if ($createSuperuser -match "^[Yy]") {
            try {
                docker-compose exec web python manage.py createsuperuser
            }
            catch {
                Write-Warning "Failed to create superuser. You can create one later."
            }
        }
        else {
            Write-Info "Skipping superuser creation. You can create one later with:"
            Write-Info "docker-compose exec web python manage.py createsuperuser"
        }
    }
}

# Show final information
function Show-CompletionInfo {
    Write-Host ""
    Write-Host "🎉 Setup Complete!" -ForegroundColor Green
    Write-Host "==================" -ForegroundColor Green
    Write-Host ""
    Write-Success "Car Rental System is now running!"
    Write-Host ""
    Write-Host "📋 Access Information:" -ForegroundColor Cyan
    Write-Host "   🌐 Application: http://localhost:8000" -ForegroundColor White
    Write-Host "   👑 Admin Panel: http://localhost:8000/admin" -ForegroundColor White
    Write-Host "   📚 API Docs:    http://localhost:8000/api/docs/" -ForegroundColor White
    Write-Host ""
    Write-Host "🐳 Docker Services:" -ForegroundColor Cyan
    Write-Host "   🔍 View logs:     docker-compose logs -f" -ForegroundColor White
    Write-Host "   ⏹️  Stop services: docker-compose down" -ForegroundColor White
    Write-Host "   🔄 Restart:       docker-compose restart" -ForegroundColor White
    Write-Host ""
    Write-Host "🛠️  Useful Commands:" -ForegroundColor Cyan
    Write-Host "   📊 Service status: docker-compose ps" -ForegroundColor White
    Write-Host "   🐚 Django shell:   docker-compose exec web python manage.py shell" -ForegroundColor White
    Write-Host "   🗄️  Database shell: docker-compose exec db psql -U car_rental_user -d car_rental_db" -ForegroundColor White
    Write-Host ""
    Write-Warning "Don't forget to:"
    Write-Host "   1. Update your .env file with real configuration" -ForegroundColor White
    Write-Host "   2. Add your Stripe keys for payment processing" -ForegroundColor White
    Write-Host "   3. Configure email settings for notifications" -ForegroundColor White
    Write-Host ""
    
    # Option to open browser
    $openBrowser = Read-Host "Would you like to open the application in your browser? (y/n)"
    if ($openBrowser -match "^[Yy]") {
        Start-Process "http://localhost:8000"
    }
}

# Main execution
function Main {
    try {
        Write-Host "Starting Car Rental System setup..." -ForegroundColor Cyan
        Write-Host ""
        
        Test-Prerequisites
        Initialize-Environment
        Start-Services
        Initialize-Database
        Show-CompletionInfo
        
        Write-Success "Setup completed successfully! 🚀"
    }
    catch {
        Write-Error "Setup failed: $($_.Exception.Message)"
        Write-Host ""
        Write-Host "🛠️  Troubleshooting:" -ForegroundColor Yellow
        Write-Host "   1. Make sure Docker Desktop is running" -ForegroundColor White
        Write-Host "   2. Check if ports 8000, 5432, 6379 are available" -ForegroundColor White
        Write-Host "   3. Try running: docker-compose down -v" -ForegroundColor White
        Write-Host "   4. Check the logs: docker-compose logs" -ForegroundColor White
        exit 1
    }
}

# Check if running as administrator (optional warning)
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "You are not running as Administrator. This may cause issues with Docker."
    Write-Host "Consider running PowerShell as Administrator if you encounter problems." -ForegroundColor Yellow
    Write-Host ""
}

# Run main function
Main
