#!/bin/bash

#############################################################
# CyberSentinel DLP - Deployment Script
# Description: Automated deployment script for production
# Usage: ./deploy.sh [install|start|stop|restart|status|logs]
#############################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="CyberSentinel DLP"
VERSION="1.0.0"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Functions
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker installed: $(docker --version)"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose installed: $(docker-compose --version)"

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker daemon is running"
}

generate_secrets() {
    print_header "Generating Secure Secrets"

    if [ ! -f "server/.env" ]; then
        print_info "Generating new secrets..."

        SECRET_KEY=$(openssl rand -hex 32)
        POSTGRES_PASSWORD=$(openssl rand -hex 16)
        MONGODB_PASSWORD=$(openssl rand -hex 16)
        REDIS_PASSWORD=$(openssl rand -hex 16)

        # Copy template
        cp config/env-templates/.env.server.example server/.env

        # Replace secrets
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" server/.env
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" server/.env
        sed -i "s/MONGODB_PASSWORD=.*/MONGODB_PASSWORD=$MONGODB_PASSWORD/" server/.env
        sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" server/.env

        # Update docker-compose.yml environment
        export POSTGRES_PASSWORD
        export MONGODB_PASSWORD
        export REDIS_PASSWORD

        print_success "Secrets generated and saved to server/.env"
        print_warning "Please backup server/.env file securely!"
    else
        print_info "Using existing server/.env file"
    fi
}

configure_dashboard() {
    print_header "Configuring Dashboard"

    if [ ! -f "dashboard/.env.local" ]; then
        # Detect host IP
        if command -v hostname &> /dev/null; then
            HOST_IP=$(hostname -I | awk '{print $1}')
        else
            HOST_IP="localhost"
        fi

        print_info "Detected host IP: $HOST_IP"

        # Create dashboard config
        cat > dashboard/.env.local << EOF
NEXT_PUBLIC_API_URL=http://$HOST_IP:8000/api/v1
NEXT_PUBLIC_APP_NAME=CyberSentinel DLP
NEXT_PUBLIC_APP_VERSION=$VERSION
NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES=true
NEXT_PUBLIC_DASHBOARD_REFRESH_INTERVAL=30000
EOF

        print_success "Dashboard configured for host IP: $HOST_IP"
        print_info "Dashboard will be accessible at: http://$HOST_IP:3000"
    else
        print_info "Using existing dashboard/.env.local file"
    fi
}

install() {
    print_header "Installing $PROJECT_NAME v$VERSION"

    check_prerequisites
    generate_secrets
    configure_dashboard

    print_header "Building Docker Images"
    docker-compose build --no-cache

    print_success "Installation complete!"
    print_info "To start the services, run: ./deploy.sh start"
}

start() {
    print_header "Starting $PROJECT_NAME"

    docker-compose up -d

    print_info "Waiting for services to be healthy..."
    sleep 15

    # Check service health
    print_header "Service Status"
    docker-compose ps

    # Get host IP
    if command -v hostname &> /dev/null; then
        HOST_IP=$(hostname -I | awk '{print $1}')
    else
        HOST_IP="localhost"
    fi

    print_success "$PROJECT_NAME started successfully!"
    echo ""
    print_info "Access the dashboard at: http://$HOST_IP:3000"
    print_info "API documentation at: http://$HOST_IP:8000/api/v1/docs"
    echo ""
    print_info "Default credentials:"
    echo "  Email: admin@cybersentinel.local"
    echo "  Password: ChangeMe123!"
    echo ""
    print_warning "Please change the default password after first login!"
}

stop() {
    print_header "Stopping $PROJECT_NAME"

    docker-compose down

    print_success "$PROJECT_NAME stopped successfully!"
}

restart() {
    print_header "Restarting $PROJECT_NAME"

    stop
    sleep 3
    start
}

status() {
    print_header "$PROJECT_NAME Status"

    docker-compose ps

    echo ""
    print_header "Service Health"

    # Check API health
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API Server: Healthy"
    else
        print_error "API Server: Not responding"
    fi

    # Check Dashboard
    if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "Dashboard: Healthy"
    else
        print_error "Dashboard: Not responding"
    fi
}

logs() {
    print_header "Viewing Logs"

    if [ -z "$2" ]; then
        docker-compose logs -f --tail=100
    else
        docker-compose logs -f --tail=100 "$2"
    fi
}

backup() {
    print_header "Creating Backup"

    BACKUP_DIR="backups"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/cybersentinel_backup_$TIMESTAMP.tar.gz"

    mkdir -p "$BACKUP_DIR"

    print_info "Backing up data..."

    # Backup PostgreSQL
    docker-compose exec -T postgres pg_dumpall -U dlp_user > "$BACKUP_DIR/postgres_$TIMESTAMP.sql"

    # Backup MongoDB
    docker-compose exec -T mongodb mongodump --archive > "$BACKUP_DIR/mongodb_$TIMESTAMP.archive"

    # Backup configuration
    tar -czf "$BACKUP_FILE" \
        server/.env \
        dashboard/.env.local \
        "$BACKUP_DIR/postgres_$TIMESTAMP.sql" \
        "$BACKUP_DIR/mongodb_$TIMESTAMP.archive" \
        config/policies/

    # Cleanup temporary files
    rm "$BACKUP_DIR/postgres_$TIMESTAMP.sql"
    rm "$BACKUP_DIR/mongodb_$TIMESTAMP.archive"

    print_success "Backup created: $BACKUP_FILE"
}

cleanup() {
    print_header "Cleaning Up"

    print_warning "This will remove all containers, volumes, and data!"
    read -p "Are you sure? (yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        docker-compose down -v
        print_success "Cleanup complete!"
    else
        print_info "Cleanup cancelled"
    fi
}

update() {
    print_header "Updating $PROJECT_NAME"

    print_info "Pulling latest changes..."
    git pull

    print_info "Rebuilding images..."
    docker-compose build --no-cache

    print_info "Restarting services..."
    restart

    print_success "Update complete!"
}

# Main script
case "$1" in
    install)
        install
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$@"
        ;;
    backup)
        backup
        ;;
    cleanup)
        cleanup
        ;;
    update)
        update
        ;;
    *)
        echo "Usage: $0 {install|start|stop|restart|status|logs|backup|cleanup|update}"
        echo ""
        echo "Commands:"
        echo "  install  - Install and configure the system"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status"
        echo "  logs     - View logs (optional: specify service name)"
        echo "  backup   - Create backup of data and configuration"
        echo "  cleanup  - Remove all containers and data (destructive)"
        echo "  update   - Update to latest version"
        exit 1
        ;;
esac

exit 0
