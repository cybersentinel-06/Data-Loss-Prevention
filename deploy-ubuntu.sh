#!/bin/bash

# =============================================================================
# CyberSentinel DLP - Ubuntu Server Deployment Script
# =============================================================================
# This script automates the deployment of CyberSentinel DLP on Ubuntu servers
# Tested on: Ubuntu 20.04, 22.04, 24.04 LTS
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if script is run as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check Ubuntu version
check_ubuntu_version() {
    log_info "Checking Ubuntu version..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" ]]; then
            log_warning "This script is designed for Ubuntu. Your OS: $ID"
            read -p "Do you want to continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
        log_success "Running on Ubuntu $VERSION"
    fi
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    apt update -y
    apt upgrade -y
    log_success "System updated"
}

# Install Docker
install_docker() {
    log_info "Checking for Docker installation..."

    if command -v docker &> /dev/null; then
        log_success "Docker is already installed: $(docker --version)"
    else
        log_info "Installing Docker..."

        # Install prerequisites
        apt install -y apt-transport-https ca-certificates curl software-properties-common gnupg lsb-release

        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

        # Set up the stable repository
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Install Docker Engine
        apt update -y
        apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        # Start and enable Docker
        systemctl start docker
        systemctl enable docker

        log_success "Docker installed successfully: $(docker --version)"
    fi
}

# Configure Docker for non-root user
configure_docker_user() {
    log_info "Configuring Docker for non-root user..."

    if [ -n "$SUDO_USER" ]; then
        usermod -aG docker $SUDO_USER
        log_success "Added $SUDO_USER to docker group"
        log_warning "User needs to log out and back in for group changes to take effect"
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."

    # Check CPU cores
    cpu_cores=$(nproc)
    log_info "CPU cores: $cpu_cores"
    if [ $cpu_cores -lt 4 ]; then
        log_warning "Less than 4 CPU cores detected. Recommended: 4+ cores"
    fi

    # Check RAM
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    log_info "Total RAM: ${total_ram}GB"
    if [ $total_ram -lt 8 ]; then
        log_warning "Less than 8GB RAM detected. Recommended: 8GB+ RAM"
    fi

    # Check disk space
    disk_space=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    log_info "Available disk space: ${disk_space}GB"
    if [ $disk_space -lt 50 ]; then
        log_warning "Less than 50GB disk space available. Recommended: 50GB+ free space"
    fi

    log_success "System requirements check completed"
}

# Create .env file
create_env_file() {
    log_info "Creating environment configuration..."

    if [ -f .env ]; then
        log_warning ".env file already exists"
        read -p "Do you want to overwrite it? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Keeping existing .env file"
            return
        fi
    fi

    # Get server IP
    default_ip=$(hostname -I | awk '{print $1}')
    read -p "Enter your Ubuntu server IP address [$default_ip]: " server_ip
    server_ip=${server_ip:-$default_ip}

    # Generate random passwords
    postgres_pass=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    mongodb_pass=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    redis_pass=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    secret_key=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-40)

    # Create .env file
    cat > .env << EOF
# CyberSentinel DLP - Production Configuration
# Generated on: $(date)

# Security Settings
SECRET_KEY=$secret_key
POSTGRES_PASSWORD=$postgres_pass
MONGODB_PASSWORD=$mongodb_pass
REDIS_PASSWORD=$redis_pass

# Network Configuration
HOST_IP=$server_ip

# Application Settings
ENVIRONMENT=production
DEBUG=False
APP_NAME=CyberSentinel DLP
APP_VERSION=1.0.0

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://0.0.0.0:3000,http://$server_ip:3000

# Database Settings
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=dlp_user
POSTGRES_DB=cybersentinel_dlp

MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_USER=dlp_user
MONGODB_DB=cybersentinel_dlp

REDIS_HOST=redis
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/cybersentinel

# Quarantine
QUARANTINE_ENABLED=true
QUARANTINE_PATH=/var/quarantine/dlp
EOF

    chmod 600 .env
    log_success ".env file created with secure random passwords"
    log_warning "IMPORTANT: Save these credentials securely!"
    echo ""
    echo "Database Credentials:"
    echo "  PostgreSQL Password: $postgres_pass"
    echo "  MongoDB Password: $mongodb_pass"
    echo "  Redis Password: $redis_pass"
    echo ""
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."

    if command -v ufw &> /dev/null; then
        # Allow SSH
        ufw allow 22/tcp

        # Allow Dashboard and API
        ufw allow 3000/tcp
        ufw allow 8000/tcp

        # Enable firewall
        echo "y" | ufw enable

        ufw status
        log_success "Firewall configured"
    else
        log_warning "UFW not installed, skipping firewall configuration"
    fi
}

# Create required directories
create_directories() {
    log_info "Creating required directories..."

    mkdir -p /var/log/cybersentinel
    mkdir -p /var/quarantine/dlp
    mkdir -p /backup/postgres
    mkdir -p /backup/mongodb

    if [ -n "$SUDO_USER" ]; then
        chown -R $SUDO_USER:$SUDO_USER /var/log/cybersentinel /var/quarantine/dlp
    fi

    log_success "Directories created"
}

# Deploy with Docker Compose
deploy_containers() {
    log_info "Deploying CyberSentinel DLP with Docker Compose..."

    # Pull images
    docker compose pull

    # Build and start containers
    docker compose up -d --build

    log_info "Waiting for services to become healthy..."
    sleep 30

    # Check container status
    docker compose ps

    log_success "Containers deployed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check if containers are running
    running_containers=$(docker compose ps --filter "status=running" --format "{{.Service}}" | wc -l)
    expected_containers=5

    if [ $running_containers -eq $expected_containers ]; then
        log_success "All $expected_containers containers are running"
    else
        log_warning "Only $running_containers out of $expected_containers containers are running"
    fi

    # Test API health
    server_ip=$(grep HOST_IP .env | cut -d '=' -f2)
    log_info "Testing API health endpoint..."
    sleep 10

    if curl -f -s http://localhost:8000/health > /dev/null; then
        log_success "API server is healthy"
    else
        log_warning "API server health check failed (may need more time to start)"
    fi

    # Display access information
    echo ""
    echo "=========================================="
    echo "  CyberSentinel DLP Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "Access URLs:"
    echo "  Dashboard: http://$server_ip:3000"
    echo "  API Server: http://$server_ip:8000"
    echo "  API Docs: http://$server_ip:8000/docs"
    echo ""
    echo "Default Credentials:"
    echo "  Username: admin"
    echo "  Password: admin"
    echo ""
    echo "Management Commands:"
    echo "  View logs:     docker compose logs -f"
    echo "  Stop system:   docker compose down"
    echo "  Start system:  docker compose up -d"
    echo "  Restart:       docker compose restart"
    echo ""
    echo "Next Steps:"
    echo "  1. Change default admin password"
    echo "  2. Configure email alerts in dashboard"
    echo "  3. Deploy agents to endpoints"
    echo "  4. Create custom DLP policies"
    echo ""
}

# Setup backup cron job
setup_backup() {
    log_info "Setting up automatic backups..."

    backup_script="/usr/local/bin/cybersentinel-backup.sh"

    cat > $backup_script << 'EOF'
#!/bin/bash
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
docker exec cybersentinel-postgres pg_dump -U dlp_user cybersentinel_dlp | gzip > /backup/postgres/backup_${BACKUP_DATE}.sql.gz
docker exec cybersentinel-mongodb mongodump --archive=/backup/mongodb/backup_${BACKUP_DATE}.archive
# Delete backups older than 30 days
find /backup/postgres -name "*.sql.gz" -mtime +30 -delete
find /backup/mongodb -name "*.archive" -mtime +30 -delete
EOF

    chmod +x $backup_script

    # Add to crontab (daily at 2 AM)
    (crontab -l 2>/dev/null; echo "0 2 * * * $backup_script") | crontab -

    log_success "Backup cron job configured (daily at 2 AM)"
}

# Main installation function
main() {
    echo ""
    echo "=========================================="
    echo "  CyberSentinel DLP - Ubuntu Deployment"
    echo "=========================================="
    echo ""

    check_root
    check_ubuntu_version

    log_info "Starting deployment process..."

    update_system
    install_docker
    configure_docker_user
    check_requirements
    create_directories
    create_env_file
    configure_firewall
    deploy_containers
    setup_backup
    verify_deployment

    log_success "Deployment completed successfully!"
}

# Run main function
main
