#!/bin/bash
# CyberSentinel DLP Agent - Linux Installation Script
# One-liner: curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/cybersentinel-dlp/main/agents/linux/install.sh | sudo bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
MANAGER_URL="${MANAGER_URL:-https://localhost:55000}"
INSTALL_DIR="${INSTALL_DIR:-/opt/cybersentinel}"
CONFIG_DIR="${CONFIG_DIR:-/etc/cybersentinel}"
SERVICE_NAME="cybersentinel-agent"

echo -e "${CYAN}========================================"
echo "CyberSentinel DLP Agent Installer v2.0"
echo -e "========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] This script must be run as root!${NC}"
    echo -e "${YELLOW}Please run with sudo: sudo bash install.sh${NC}"
    exit 1
fi

# Parse arguments
UNINSTALL=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --manager-url)
            MANAGER_URL="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Uninstall mode
if [ "$UNINSTALL" = true ]; then
    echo -e "${YELLOW}[*] Uninstalling CyberSentinel DLP Agent...${NC}"

    # Stop service
    if systemctl is-active --quiet $SERVICE_NAME; then
        systemctl stop $SERVICE_NAME
        echo -e "${GREEN}[+] Service stopped${NC}"
    fi

    # Disable service
    if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
        systemctl disable $SERVICE_NAME
        echo -e "${GREEN}[+] Service disabled${NC}"
    fi

    # Remove service file
    if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        systemctl daemon-reload
        echo -e "${GREEN}[+] Service file removed${NC}"
    fi

    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}[+] Installation directory removed${NC}"
    fi

    # Ask about configuration
    if [ -d "$CONFIG_DIR" ]; then
        read -p "Remove configuration directory? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$CONFIG_DIR"
            echo -e "${GREEN}[+] Configuration directory removed${NC}"
        fi
    fi

    echo ""
    echo -e "${GREEN}[+] Uninstallation complete!${NC}"
    exit 0
fi

# Installation mode
echo -e "${YELLOW}[*] Installing CyberSentinel DLP Agent...${NC}"
echo -e "    Manager URL: ${MANAGER_URL}"
echo -e "    Install Dir: ${INSTALL_DIR}"
echo -e "    Config Dir:  ${CONFIG_DIR}"
echo ""

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    VERSION=$VERSION_ID
else
    DISTRO="unknown"
fi

echo -e "${CYAN}[1/9] Checking system requirements...${NC}"
echo -e "    Distribution: $DISTRO $VERSION"
echo -e "    Architecture: $(uname -m)"

# Check Python
echo -e "${CYAN}[2/9] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed!${NC}"
    echo -e "${YELLOW}Installing Python 3...${NC}"

    case $DISTRO in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y python3 python3-pip python3-dev
            ;;
        centos|rhel|fedora)
            yum install -y python3 python3-pip python3-devel
            ;;
        arch)
            pacman -Sy --noconfirm python python-pip
            ;;
        *)
            echo -e "${RED}[ERROR] Unsupported distribution: $DISTRO${NC}"
            echo -e "${YELLOW}Please install Python 3.8+ manually${NC}"
            exit 1
            ;;
    esac
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}[+] Python version: $PYTHON_VERSION${NC}"

# Check Python version (need 3.8+)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}[ERROR] Python 3.8+ is required (found: $PYTHON_VERSION)${NC}"
    exit 1
fi

# Install system dependencies
echo -e "${CYAN}[3/9] Installing system dependencies...${NC}"

case $DISTRO in
    ubuntu|debian)
        apt-get install -y \
            python3-dev \
            python3-pip \
            libx11-dev \
            libudev-dev \
            pkg-config \
            gcc \
            curl
        ;;
    centos|rhel|fedora)
        yum install -y \
            python3-devel \
            python3-pip \
            libX11-devel \
            libudev-devel \
            pkgconfig \
            gcc \
            curl
        ;;
    arch)
        pacman -Sy --noconfirm \
            python-pip \
            libx11 \
            systemd \
            gcc \
            curl
        ;;
esac

echo -e "${GREEN}[+] System dependencies installed${NC}"

# Create directories
echo -e "${CYAN}[4/9] Creating directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$CONFIG_DIR/logs"
echo -e "${GREEN}[+] Directories created${NC}"

# Download agent files
echo -e "${CYAN}[5/9] Downloading agent files...${NC}"

# Create directory structure
mkdir -p "$INSTALL_DIR/common/monitors"
mkdir -p "$INSTALL_DIR/linux"

# For local testing, copy from current directory
# For production, download from GitHub
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -d "$SCRIPT_DIR/common" ]; then
    echo -e "${YELLOW}[*] Using local installation${NC}"
    cp -r "$SCRIPT_DIR/common"/* "$INSTALL_DIR/common/"
    cp -r "$SCRIPT_DIR/linux"/* "$INSTALL_DIR/linux/"
    cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
else
    echo -e "${YELLOW}[*] Downloading from repository${NC}"
    # TODO: Download from GitHub when published
    echo -e "${RED}[ERROR] Remote installation not yet implemented${NC}"
    echo -e "${YELLOW}Please run from the agents directory${NC}"
    exit 1
fi

echo -e "${GREEN}[+] Agent files installed${NC}"

# Install Python dependencies
echo -e "${CYAN}[6/9] Installing Python dependencies...${NC}"
python3 -m pip install --upgrade pip -q
python3 -m pip install -r "$INSTALL_DIR/requirements.txt" -q
echo -e "${GREEN}[+] Python dependencies installed${NC}"

# Create configuration file
echo -e "${CYAN}[7/9] Creating configuration file...${NC}"

HOSTNAME=$(hostname)
USERNAME=$(who | awk 'NR==1{print $1}')

cat > "$CONFIG_DIR/agent.yml" << EOF
# CyberSentinel DLP Agent Configuration
# Auto-generated on $(date '+%Y-%m-%d %H:%M:%S')

agent:
  id: ""  # Auto-assigned by manager
  name: "$HOSTNAME"
  manager_url: "$MANAGER_URL"
  registration_key: ""  # Auto-generated after registration
  heartbeat_interval: 60  # seconds

monitoring:
  file_system:
    enabled: true
    paths:
      - "/home/$USERNAME/Desktop"
      - "/home/$USERNAME/Documents"
      - "/home/$USERNAME/Downloads"
    extensions:
      - .pdf
      - .docx
      - .xlsx
      - .txt
      - .csv
      - .pptx
    exclude_patterns:
      - "*/node_modules/*"
      - "*/.git/*"
      - "*/venv/*"

  clipboard:
    enabled: true
    poll_interval: 2  # seconds

  usb:
    enabled: true
    poll_interval: 5  # seconds

  network:
    enabled: false

classification:
  local:
    enabled: true
    patterns:
      - credit_card
      - ssn
      - email

performance:
  max_events_per_minute: 100
  max_event_size: 1048576  # 1MB
  batch_size: 10
  queue_size: 1000

logging:
  level: INFO
  file: "$CONFIG_DIR/logs/agent.log"
  max_size: 10485760  # 10MB
  max_files: 5
EOF

echo -e "${GREEN}[+] Configuration file created: $CONFIG_DIR/agent.yml${NC}"

# Create systemd service
echo -e "${CYAN}[8/9] Creating systemd service...${NC}"

cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=CyberSentinel DLP Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PYTHONUNBUFFERED=1"
Environment="CYBERSENTINEL_CONFIG=$CONFIG_DIR/agent.yml"
ExecStart=/usr/bin/python3 $INSTALL_DIR/linux/agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo -e "${GREEN}[+] Systemd service created${NC}"

# Test connection to manager
echo -e "${CYAN}[9/9] Testing connection to manager...${NC}"
echo -e "    Manager URL: $MANAGER_URL"

if curl -k -s -f "$MANAGER_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}[+] Manager is reachable${NC}"
else
    echo -e "${YELLOW}[-] Warning: Cannot reach manager at $MANAGER_URL${NC}"
    echo -e "    Agent will attempt registration on first start"
fi

# Enable and start service
echo -e "${YELLOW}[*] Starting agent service...${NC}"
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Wait a moment and check status
sleep 2

if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}[+] Agent service started successfully${NC}"
else
    echo -e "${RED}[-] Agent service failed to start${NC}"
    echo -e "${YELLOW}Check logs with: journalctl -u $SERVICE_NAME -f${NC}"
fi

echo ""
echo -e "${GREEN}========================================"
echo "Installation Complete!"
echo -e "========================================${NC}"
echo ""
echo -e "${CYAN}Agent Details:${NC}"
echo -e "  - Install Directory: $INSTALL_DIR"
echo -e "  - Config File: $CONFIG_DIR/agent.yml"
echo -e "  - Manager URL: $MANAGER_URL"
echo ""
echo -e "${CYAN}The agent will automatically:${NC}"
echo -e "  1. Register with the manager"
echo -e "  2. Start monitoring file system, clipboard, and USB"
echo -e "  3. Send events to the manager"
echo ""
echo -e "${CYAN}Useful commands:${NC}"
echo -e "  - Check status:  systemctl status $SERVICE_NAME"
echo -e "  - View logs:     journalctl -u $SERVICE_NAME -f"
echo -e "  - Restart:       systemctl restart $SERVICE_NAME"
echo -e "  - Stop:          systemctl stop $SERVICE_NAME"
echo -e "  - Uninstall:     curl -fsSL URL/install.sh | sudo bash -s -- --uninstall"
echo ""
echo -e "View logs at: $CONFIG_DIR/logs/agent.log"
echo ""
