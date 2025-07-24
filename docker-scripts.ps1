# Docker Management Scripts for Car Rental System
# PowerShell script for Windows development

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "prod", "build", "clean", "logs", "shell", "test", "backup", "restore")]
    [string]$Action,
    
    [string]$Service = "web"
)

function Write-Info {
    param([string]$Message)
    Write-Host "🚀 $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

switch ($Action) {
    "dev" {
        Write-Info "Starting development environment..."
        docker-compose up --build
    }
    
    "prod" {
        Write-Info "Starting production environment..."
        if (-not (Test-Path ".env.prod")) {
            Write-Error ".env.prod file not found. Please create it first."
            exit 1
        }
        docker-compose -f docker-compose.prod.yml up --build -d
        Write-Info "Production environment started. Access at http://localhost"
        Write-Info "Flower monitoring available at http://localhost:5555"
    }
    
    "build" {
        Write-Info "Building Docker images..."
        docker-compose build --no-cache
    }
    
    "clean" {
        Write-Info "Cleaning up Docker resources..."
        docker-compose down -v
        docker system prune -f
        docker volume prune -f
        Write-Info "Cleanup completed"
    }
    
    "logs" {
        Write-Info "Showing logs for service: $Service"
        docker-compose logs -f $Service
    }
    
    "shell" {
        Write-Info "Opening shell in $Service container..."
        docker-compose exec $Service /bin/bash
    }
    
    "test" {
        Write-Info "Running tests..."
        docker-compose exec web python manage.py test
    }
    
    "backup" {
        Write-Info "Creating database backup..."
        $BackupFile = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
        docker-compose exec db pg_dump -U car_rental_user car_rental_db > "./backups/$BackupFile"
        Write-Info "Backup created: ./backups/$BackupFile"
    }
    
    "restore" {
        Write-Info "Database restore requires manual file specification"
        Write-Host "Usage: docker-compose exec db psql -U car_rental_user car_rental_db < ./backups/your_backup.sql"
    }
}

# Additional helpful commands
Write-Host "`n📋 Available commands:" -ForegroundColor Yellow
Write-Host "  dev     - Start development environment"
Write-Host "  prod    - Start production environment"
Write-Host "  build   - Build Docker images"
Write-Host "  clean   - Clean up Docker resources"
Write-Host "  logs    - Show logs (specify -Service)"
Write-Host "  shell   - Open shell in container (specify -Service)"
Write-Host "  test    - Run Django tests"
Write-Host "  backup  - Create database backup"
Write-Host "  restore - Show restore instructions"
Write-Host "`nExample: ./docker-scripts.ps1 -Action dev"
Write-Host "Example: ./docker-scripts.ps1 -Action logs -Service db"
