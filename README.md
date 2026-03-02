# CyberSentinel DLP

**Enterprise-Grade Data Loss Prevention Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docs.docker.com/compose/)

A production-ready Data Loss Prevention platform with real-time endpoint monitoring, cloud storage integration (Google Drive, OneDrive), automated policy enforcement, SIEM forwarding, and a React dashboard — deployable with a single command.

---

## Table of Contents

- [Quick Start — One-Command Install](#quick-start--one-command-install)
- [Architecture](#architecture)
- [Features](#features)
- [Step-by-Step Installation Guide](#step-by-step-installation-guide)
  - [Prerequisites](#1-prerequisites)
  - [Server Deployment (Docker)](#2-server-deployment-docker)
  - [Post-Deployment Configuration](#3-post-deployment-configuration)
  - [Windows Agent Installation](#4-windows-agent-installation)
  - [Linux Agent Installation](#5-linux-agent-installation)
  - [Cloud Storage Integration](#6-cloud-storage-integration)
  - [SIEM Integration (Optional)](#7-siem-integration-optional)
- [Agent Configuration Reference](#agent-configuration-reference)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Management & Operations](#management--operations)
- [Troubleshooting](#troubleshooting)
- [Technology Stack](#technology-stack)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start — One-Command Install

Run this on any machine with **Python 3.8+** and **Docker**:

```bash
curl -sLO https://raw.githubusercontent.com/cybersentinel-06/Data-Loss-Prevention/main/install_dlp_server.py && python3 install_dlp_server.py
```

This will:
1. Download `docker-compose.yml`, `.env.example`, and DB init script (3 files total)
2. Generate `.env` with random secrets and auto-detected host IP
3. Pull pre-built images from GitHub Container Registry
4. Start the full stack (PostgreSQL, MongoDB, Redis, OpenSearch, FastAPI, React dashboard)

No source code checkout. No build step. Just pull and run.

> Add `--no-start` to download and configure only without starting services.
> Use `python3 install_dlp_server.py /opt/cybersentinel` to install to a custom path.

| Service | Default URL |
|---|---|
| Dashboard | `http://<server-ip>:3000` |
| API Server | `http://<server-ip>:55000` |
| API Docs (Swagger) | `http://<server-ip>:55000/docs` |

**Default credentials:** username `admin` / password `admin` (created automatically on first boot)

---

## Architecture

```
                        ┌──────────────────────────────────────────────────────┐
                        │              DLP Management Server                   │
                        │                                                      │
  ┌──────────┐          │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
  │ React    │ :3000    │  │ FastAPI  │  │  Celery  │  │  Celery  │          │
  │Dashboard ├─────────►│  │  API     │  │  Worker  │  │   Beat   │          │
  │ (nginx)  │  /api/   │  │  :55000  │  │          │  │          │          │
  └──────────┘ proxy    │  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
                        │       │              │              │                │
                        │  ┌────▼────┐  ┌─────▼────┐  ┌─────▼─────┐  ┌─────┐│
                        │  │PostgreSQL│  │  Redis   │  │ OpenSearch │  │Mongo││
                        │  │  :5432  │  │  :6379   │  │   :9200   │  │:27017││
                        │  └─────────┘  └──────────┘  └───────────┘  └─────┘│
                        └──────────────────────────────────────────────────────┘
                                              ▲
                                              │ HTTPS / REST
                          ┌───────────────────┼───────────────────┐
                          │                   │                   │
                   ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
                   │   Windows   │     │    Linux    │     │   Cloud     │
                   │   Agent     │     │    Agent    │     │  Connectors │
                   │             │     │             │     │             │
                   │ File System │     │ File System │     │Google Drive │
                   │ Clipboard   │     │ File Xfer   │     │  OneDrive   │
                   │ USB Monitor │     │             │     │             │
                   │ File Xfer   │     │             │     │             │
                   └─────────────┘     └─────────────┘     └─────────────┘
```

**Components:**

| Component | Purpose | Technology |
|---|---|---|
| API Server | Central management, event processing, policy evaluation | FastAPI + Uvicorn |
| Dashboard | Web UI for monitoring, policies, alerts | React 18 + Vite + Nginx |
| PostgreSQL | Users, agents, policies, alerts, cloud connections | PostgreSQL 15 |
| MongoDB | Event document storage | MongoDB 7 |
| Redis | Caching, sessions, token blacklist, Celery broker | Redis 7 |
| OpenSearch | Full-text event search and analytics | OpenSearch 2.11 |
| Celery Worker | Background tasks (Google Drive/OneDrive polling, reports) | Celery 5.3 |
| Celery Beat | Scheduled task execution | Celery Beat |
| Windows Agent | Endpoint monitoring (files, clipboard, USB) | Python + watchdog + pywin32 |
| Linux Agent | Endpoint monitoring (files, transfers) | Python + watchdog |

---

## Features

### Endpoint Monitoring
- **File System Monitoring** — Real-time detection of file create, modify, move, delete
- **Clipboard Monitoring** — Captures clipboard content for PII scanning (Windows)
- **USB Device Detection** — Logs USB connect/disconnect events (Windows)
- **USB File Transfer Blocking** — Block or quarantine copies to removable drives (Windows)
- **File Transfer Monitoring** — Detect and block copies from protected paths to monitored destinations

### Cloud Storage Integration
- **Google Drive** — OAuth connection, folder-level monitoring, activity polling, baseline tracking
- **OneDrive** — OAuth connection, Microsoft Graph delta queries, hybrid modification detection

### Policy Engine
- **Policy Types:** File system, clipboard, USB device, USB transfer, file transfer, Google Drive (local + cloud), OneDrive cloud
- **Actions:** Log, alert, block (delete), quarantine (move to quarantine folder)
- **Agent Scoping** — Assign policies to specific agents or all agents
- **Priority & Severity** — Configurable per policy
- **Versioned Bundles** — Agents fetch policy updates via versioned sync

### PII Detection & Classification
- Credit cards (Luhn validation)
- Social Security Numbers
- Email addresses, phone numbers
- API keys and secrets (AWS, GitHub, Stripe, OpenAI)
- Healthcare data (HIPAA), Financial data (PCI-DSS)

### Alerting & Analytics
- Real-time alert creation from policy violations
- Alert lifecycle: New → Acknowledged → Investigating → Resolved
- Time-series incident trends and top violators
- CSV and PDF report export

### SIEM Integration
- Splunk Enterprise/Cloud connector
- Elasticsearch/ELK Stack connector
- Batch event forwarding

### Compliance
- GDPR (EU data protection)
- HIPAA (healthcare)
- PCI-DSS (payment cards)
- SOX (financial reporting)

---

## Step-by-Step Installation Guide

### 1. Prerequisites

#### Server Requirements

| Requirement | Minimum |
|---|---|
| OS | Ubuntu 20.04+, Debian 11+, RHEL 8+, or any Linux with Docker |
| CPU | 2 cores |
| RAM | 4 GB (8 GB recommended) |
| Disk | 20 GB free |
| Docker | 20.10+ |
| Docker Compose | v2.0+ (plugin or standalone) |
| Python | 3.8+ (for the installer script only) |
| Network | Ports 3000 (dashboard) and 55000 (API) accessible from agents |

#### Agent Requirements

| Requirement | Windows | Linux |
|---|---|---|
| OS | Windows 10/11 or Server 2016+ | Ubuntu 20.04+, Debian 11+, RHEL 8+ |
| Python | 3.8+ | 3.8+ |
| Network | Outbound HTTPS to server:55000 | Same |

#### Install Docker (if not present)

```bash
# Ubuntu / Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect

# Verify
docker --version
docker compose version
```

---

### 2. Server Deployment (Docker)

#### Option A: One-Command Install (Recommended)

```bash
curl -sLO https://raw.githubusercontent.com/cybersentinel-06/Data-Loss-Prevention/main/install_dlp_server.py && python3 install_dlp_server.py
```

The script will:
- Create a `cybersentinel-dlp/` directory
- Download `docker-compose.yml`, `.env.example`, and the DB init SQL
- Generate `.env` with random passwords and your server's IP
- Pull pre-built images from `ghcr.io/cybersentinel-06`
- Start all 8 services

**To install to a custom directory:**
```bash
python3 install_dlp_server.py /opt/cybersentinel
```

**To download and configure only (start manually later):**
```bash
python3 install_dlp_server.py --no-start
cd cybersentinel-dlp
# Edit .env if needed
docker compose up -d
```

#### Option B: Manual Setup

```bash
# 1. Create a directory and download the 3 required files
mkdir cybersentinel-dlp && cd cybersentinel-dlp
mkdir -p init-scripts

BASE="https://raw.githubusercontent.com/cybersentinel-06/Data-Loss-Prevention/main"
curl -sLO "$BASE/docker-compose.deploy.yml" && mv docker-compose.deploy.yml docker-compose.yml
curl -sLO "$BASE/.env.example"
curl -sL  "$BASE/database/postgresql/init/01-init.sql" -o init-scripts/01-init.sql

# 2. Create .env from the example
cp .env.example .env

# 3. Edit .env — at minimum, set passwords and your server IP
nano .env
#   SECRET_KEY=<random 32+ char string>
#   POSTGRES_PASSWORD=<strong password>
#   MONGODB_PASSWORD=<strong password>
#   REDIS_PASSWORD=<strong password>
#   HOST_IP=<your server IP>
#   VITE_API_URL=http://<your server IP>:55000/api/v1
#   CORS_ORIGINS=["http://<your server IP>:3000"]

# 4. Start services
docker compose up -d
```

#### Verify Deployment

```bash
# Check all containers are running
docker compose ps

# Test API health
curl http://localhost:55000/health
# Expected: {"status":"healthy"}

# Test readiness (checks all DB connections)
curl http://localhost:55000/ready

# Open dashboard in browser
# http://<server-ip>:3000
```

You should see 8 containers: postgres, mongodb, redis, opensearch, manager, celery-worker, celery-beat, dashboard.

---

### 3. Post-Deployment Configuration

#### Change the Default Admin Password

1. Open `http://<server-ip>:3000` in your browser
2. Log in with username `admin` and password `admin`
3. Navigate to **Settings** or **Users** and change the admin password immediately

#### Create Your First Policy

1. Go to **Policies** in the dashboard
2. Click **Create Policy**
3. Select a policy type (e.g., File System Monitoring)
4. Configure:
   - **Name:** e.g., "Monitor Documents Folder"
   - **Severity:** High
   - **Monitored Paths:** e.g., `/home/user/Documents`
   - **File Extensions:** `.pdf, .docx, .xlsx, .csv`
   - **Action:** Alert (or Block/Quarantine)
5. **Enable** the policy
6. Optionally scope it to specific agents via the Agent IDs field

#### Customize Environment (Optional)

Edit `.env` and restart to apply changes:

```bash
nano .env
docker compose down && docker compose up -d
```

Key settings to review:
- `CORS_ORIGINS` — Add all URLs that access the dashboard
- `SMTP_*` — Enable email alerts
- `COMPLIANCE_MODE` — Set applicable frameworks (GDPR, HIPAA, PCI-DSS)
- `DATA_RETENTION_DAYS` — How long to keep events (default: 90)

---

### 4. Windows Agent Installation

#### Option A: PowerShell Installer (Recommended)

Run in an **elevated PowerShell** (Run as Administrator):

```powershell
# Download and run the installer
# -ManagerUrl: point to your DLP server
cd C:\Temp
git clone https://github.com/cybersentinel-06/Data-Loss-Prevention.git
cd Data-Loss-Prevention\scripts
.\install_windows_agent.ps1 -ManagerUrl "http://<SERVER-IP>:55000/api/v1"
```

The installer will:
- Create a Python virtual environment
- Install dependencies from `agents/endpoint/windows/requirements.txt`
- Copy `agent_config.json` to `C:\ProgramData\CyberSentinel\`
- Register a Windows Scheduled Task (`CyberSentinelAgent`) that starts at boot

#### Option B: Manual Installation

```powershell
# 1. Clone the repository
git clone https://github.com/cybersentinel-06/Data-Loss-Prevention.git
cd Data-Loss-Prevention\agents\endpoint\windows

# 2. Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt

# 3. Copy and edit the config file
mkdir -Force C:\ProgramData\CyberSentinel
Copy-Item agent_config.json C:\ProgramData\CyberSentinel\agent_config.json
notepad C:\ProgramData\CyberSentinel\agent_config.json
# Set: "server_url": "http://<SERVER-IP>:55000/api/v1"

# 4. Run the agent
python agent.py
```

#### Install as Windows Service (NSSM)

```powershell
# Install NSSM
choco install nssm -y

# Register the service
nssm install CyberSentinelAgent "C:\...\Data-Loss-Prevention\agents\endpoint\windows\.venv\Scripts\python.exe" "C:\...\Data-Loss-Prevention\agents\endpoint\windows\agent.py"
nssm set CyberSentinelAgent AppDirectory "C:\...\Data-Loss-Prevention\agents\endpoint\windows"
nssm set CyberSentinelAgent Start SERVICE_AUTO_START
nssm start CyberSentinelAgent
```

#### Verify Windows Agent

```powershell
# Check logs
Get-Content "C:\ProgramData\CyberSentinel\cybersentinel_agent.log" -Tail 20

# Test connectivity to server
Test-NetConnection -ComputerName <SERVER-IP> -Port 55000

# The agent should appear in Dashboard > Agents within 30 seconds
```

**Windows Agent Capabilities:**

| Feature | Status |
|---|---|
| File System Monitoring | Watches configured paths for create/modify/move/delete |
| Clipboard Monitoring | Captures text clipboard, classifies for PII |
| USB Device Monitoring | Logs USB connect/disconnect events |
| USB File Transfer | Detects copies to removable drives; can block or quarantine |
| File Transfer Blocking | Blocks copies from protected paths to monitored destinations |
| Google Drive Local Mirror | Monitors `G:\My Drive\...` paths from policies |

---

### 5. Linux Agent Installation

#### Option A: Automated Installer (Recommended)

```bash
git clone https://github.com/cybersentinel-06/Data-Loss-Prevention.git
cd Data-Loss-Prevention/agents/endpoint/linux

# Edit config FIRST — set server_url
nano agent_config.json
# Set: "server_url": "http://<SERVER-IP>:55000/api/v1"

# Run the installer (requires root)
sudo chmod +x install.sh
sudo ./install.sh
```

The installer will:
1. Install Python 3 and pip
2. Install dependencies from `requirements.txt`
3. Copy `agent.py` to `/opt/cybersentinel/`
4. Copy `agent_config.json` to `/etc/cybersentinel/`
5. Install and enable the `cybersentinel-agent` systemd service

#### Option B: Manual Installation

```bash
cd Data-Loss-Prevention/agents/endpoint/linux

# 1. Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Copy and configure
sudo mkdir -p /etc/cybersentinel
sudo cp agent_config.json /etc/cybersentinel/agent_config.json
sudo nano /etc/cybersentinel/agent_config.json
# Set: "server_url": "http://<SERVER-IP>:55000/api/v1"

# 3. Run the agent
python3 agent.py
```

#### Install as systemd Service (Manual)

```bash
sudo cp cybersentinel-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cybersentinel-agent
sudo systemctl start cybersentinel-agent
```

#### Verify Linux Agent

```bash
# Check service status
sudo systemctl status cybersentinel-agent

# View logs
sudo journalctl -u cybersentinel-agent -f
# or
tail -f /var/log/cybersentinel_agent.log

# Test connectivity
curl http://<SERVER-IP>:55000/health
```

**Linux Agent Capabilities:**

| Feature | Status |
|---|---|
| File System Monitoring | Watches configured paths for create/modify/move/delete |
| File Transfer Monitoring | Blocks or quarantines copies from protected paths |
| Clipboard Monitoring | Not implemented |
| USB Monitoring | Not implemented |

---

### 6. Cloud Storage Integration

#### Google Drive Setup

1. **Create Google Cloud OAuth Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project (or select existing)
   - Enable the **Google Drive Activity API** and **Google Drive API**
   - Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
   - Application type: **Web application**
   - Authorized redirect URI: `http://<SERVER-IP>:55000/api/v1/google-drive/callback`
   - Download the client ID and secret

2. **Connect in the Dashboard:**
   - Go to **Dashboard** → **Settings** or the **Google Drive** section
   - Click **Connect Google Drive**
   - Authenticate with your Google account
   - Select folders to monitor

3. **Polling:** The Celery Beat scheduler automatically polls for changes. You can also trigger a manual poll from the dashboard.

#### OneDrive Setup

1. **Register an Azure AD Application:**
   - Go to [Azure Portal](https://portal.azure.com/) → **Azure Active Directory** → **App registrations**
   - Click **New registration**
   - Redirect URI: `http://<SERVER-IP>:55000/api/v1/onedrive/callback`
   - Under **API permissions**, add:
     - `Files.Read.All`
     - `Sites.Read.All`
     - `User.Read`
   - Under **Certificates & secrets**, create a new client secret

2. **Add to `.env`:**
   ```bash
   ONEDRIVE_CLIENT_ID=<your-app-client-id>
   ONEDRIVE_CLIENT_SECRET=<your-client-secret>
   ONEDRIVE_REDIRECT_URI=http://<SERVER-IP>:55000/api/v1/onedrive/callback
   ONEDRIVE_TENANT_ID=common   # or your specific tenant ID
   ```
   Restart services: `docker compose down && docker compose up -d`

3. **Connect in the Dashboard:**
   - Go to the **OneDrive** section
   - Click **Connect OneDrive**
   - Authenticate with your Microsoft account
   - Select folders to monitor

---

### 7. SIEM Integration (Optional)

#### Splunk

Configure in the dashboard under **Settings** → **SIEM Integration** or via the API:

```bash
curl -X POST "http://<SERVER-IP>:55000/api/v1/siem/connectors" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "splunk",
    "host": "splunk-server.company.com",
    "port": 8089,
    "token": "your-splunk-hec-token"
  }'
```

#### Elasticsearch / ELK

```bash
curl -X POST "http://<SERVER-IP>:55000/api/v1/siem/connectors" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "elasticsearch",
    "host": "elk-server.company.com",
    "port": 9200
  }'
```

---

## Agent Configuration Reference

Both agents use `agent_config.json`:

```json
{
  "server_url": "http://<SERVER-IP>:55000/api/v1",
  "agent_id": "",
  "agent_name": "my-endpoint",
  "heartbeat_interval": 30,
  "policy_sync_interval": 60,
  "monitoring": {
    "file_system": true,
    "clipboard": true,
    "usb_devices": true,
    "monitored_paths": [
      "C:\\Users\\<user>\\Documents",
      "C:\\Users\\<user>\\Desktop",
      "C:\\Users\\<user>\\Downloads"
    ],
    "exclude_paths": [],
    "file_extensions": [".pdf", ".docx", ".xlsx", ".csv", ".txt", ".pptx"],
    "transfer_blocking": {
      "enabled": false,
      "block_removable_drives": true,
      "poll_interval_seconds": 5
    }
  },
  "quarantine": {
    "enabled": true,
    "folder": "C:\\Quarantine"
  },
  "classification": {
    "enabled": true,
    "max_file_size_mb": 10
  },
  "performance": {
    "max_events_per_minute": 100,
    "batch_size": 10,
    "queue_size": 1000
  },
  "logging": {
    "level": "INFO",
    "file": "C:\\ProgramData\\CyberSentinel\\cybersentinel_agent.log"
  }
}
```

| Field | Description | Default |
|---|---|---|
| `server_url` | DLP server API endpoint | Required |
| `agent_id` | Auto-generated on first registration | Auto |
| `agent_name` | Display name in dashboard | Hostname |
| `heartbeat_interval` | Seconds between heartbeats | 30 |
| `policy_sync_interval` | Seconds between policy fetches | 60 |
| `monitoring.file_system` | Enable file system watcher | true |
| `monitoring.clipboard` | Enable clipboard monitoring (Windows only) | true |
| `monitoring.usb_devices` | Enable USB detection (Windows only) | true |
| `monitoring.monitored_paths` | Paths to watch | See above |
| `monitoring.file_extensions` | File types to classify | See above |
| `monitoring.transfer_blocking.enabled` | Block unauthorized transfers | false |
| `quarantine.enabled` | Move violations to quarantine folder | true |
| `quarantine.folder` | Quarantine directory path | OS-specific |
| `classification.max_file_size_mb` | Max file size for PII scanning | 10 |

---

## API Reference

The API is fully documented via Swagger at `http://<server-ip>:55000/docs`.

### Authentication

```bash
# Login — returns access_token and refresh_token
curl -X POST "http://<server-ip>:55000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"

# Use the token for all subsequent requests
curl -H "Authorization: Bearer <access_token>" http://<server-ip>:55000/api/v1/agents/
```

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| **Auth** | | |
| POST | `/api/v1/auth/login` | Login (returns JWT) |
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/refresh` | Refresh token |
| **Agents** | | |
| POST | `/api/v1/agents/register` | Register agent |
| GET | `/api/v1/agents/` | List agents |
| POST | `/api/v1/agents/{id}/heartbeat` | Agent heartbeat |
| GET | `/api/v1/agents/{id}/policies` | Get agent policy bundle |
| **Events** | | |
| POST | `/api/v1/events/` | Submit event (from agents) |
| GET | `/api/v1/events/` | Query events (filters, pagination) |
| GET | `/api/v1/events/stats/summary` | Event statistics |
| **Policies** | | |
| POST | `/api/v1/policies/` | Create policy |
| GET | `/api/v1/policies/` | List policies |
| PATCH | `/api/v1/policies/{id}` | Update policy |
| DELETE | `/api/v1/policies/{id}` | Delete policy |
| **Alerts** | | |
| GET | `/api/v1/alerts/` | List alerts |
| PATCH | `/api/v1/alerts/{id}` | Update alert status |
| **Dashboard** | | |
| GET | `/api/v1/dashboard/overview` | Overview statistics |
| GET | `/api/v1/dashboard/timeline` | Event timeline |
| **Analytics** | | |
| GET | `/api/v1/analytics/events` | Event analytics |
| GET | `/api/v1/analytics/top-violators` | Top violators |
| **Google Drive** | | |
| POST | `/api/v1/google-drive/connect` | Start OAuth |
| GET | `/api/v1/google-drive/connections` | List connections |
| POST | `/api/v1/google-drive/poll` | Trigger poll |
| **OneDrive** | | |
| POST | `/api/v1/onedrive/connect` | Start OAuth |
| GET | `/api/v1/onedrive/connections` | List connections |
| POST | `/api/v1/onedrive/poll` | Trigger poll |
| **Export** | | |
| POST | `/api/v1/export/events/csv` | Export events CSV |
| POST | `/api/v1/export/events/pdf` | Export events PDF |
| **SIEM** | | |
| GET | `/api/v1/siem/status` | SIEM connection status |
| POST | `/api/v1/siem/send-events` | Forward events to SIEM |
| **Health** | | |
| GET | `/health` | Liveness check |
| GET | `/ready` | Readiness check (DB connectivity) |
| GET | `/metrics` | Prometheus metrics |

---

## Environment Variables

All configuration is through the `.env` file. The installer generates one automatically with random secrets.

### Required

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | JWT signing key (32+ chars) | Auto-generated |
| `POSTGRES_PASSWORD` | PostgreSQL password | Auto-generated |
| `MONGODB_PASSWORD` | MongoDB password | Auto-generated |
| `REDIS_PASSWORD` | Redis password | Auto-generated |

### Network

| Variable | Description | Default |
|---|---|---|
| `HOST_IP` | Server's LAN IP | Auto-detected |
| `VITE_API_URL` | Dashboard → API URL | `http://<ip>:55000/api/v1` |
| `CORS_ORIGINS` | Allowed dashboard origins (JSON list or CSV) | `["http://localhost:3000"]` |
| `ALLOWED_HOSTS` | Trusted hosts | `["localhost","127.0.0.1"]` |

### Application

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | `production` or `development` | `production` |
| `DEBUG` | Enable debug mode | `False` |
| `PORT` | API server port | `55000` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Databases

| Variable | Default | Notes |
|---|---|---|
| `POSTGRES_HOST` | `postgres` | Docker service name |
| `POSTGRES_PORT` | `5432` | |
| `MONGODB_HOST` | `mongodb` | Docker service name |
| `MONGODB_PORT` | `27017` | |
| `REDIS_HOST` | `redis` | Docker service name |
| `REDIS_PORT` | `6379` | |
| `OPENSEARCH_HOST` | `opensearch` | Docker service name |
| `OPENSEARCH_PORT` | `9200` | |

### Optional Integrations

| Variable | Description | Default |
|---|---|---|
| `SMTP_ENABLED` | Enable email alerts | `false` |
| `SMTP_HOST` | SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username | |
| `SMTP_PASSWORD` | SMTP password | |
| `ONEDRIVE_CLIENT_ID` | Azure AD app client ID | |
| `ONEDRIVE_CLIENT_SECRET` | Azure AD app secret | |
| `ONEDRIVE_TENANT_ID` | Azure AD tenant | `common` |
| `COMPLIANCE_MODE` | Active frameworks | `GDPR,HIPAA,PCI-DSS` |
| `DATA_RETENTION_DAYS` | Event retention period | `90` |
| `QUARANTINE_ENABLED` | Enable file quarantine | `true` |

---

## Management & Operations

### Service Management

```bash
cd cybersentinel-dlp   # or wherever you installed

# Status
docker compose ps

# Logs (all services)
docker compose logs -f

# Logs (specific service)
docker compose logs -f manager
docker compose logs -f dashboard
docker compose logs -f celery-worker

# Stop
docker compose down

# Start
docker compose up -d

# Restart a single service
docker compose restart manager

# Update to latest images
docker compose pull && docker compose up -d
```

### Backup

```bash
# Backup PostgreSQL
docker compose exec postgres pg_dumpall -U dlp_user > backup_postgres_$(date +%Y%m%d).sql

# Backup MongoDB
docker compose exec mongodb mongodump --archive > backup_mongo_$(date +%Y%m%d).archive

# Backup .env (contains secrets)
cp .env .env.backup
```

### Restore

```bash
# Restore PostgreSQL
cat backup_postgres_20260302.sql | docker compose exec -T postgres psql -U dlp_user

# Restore MongoDB
cat backup_mongo_20260302.archive | docker compose exec -T mongodb mongorestore --archive
```

---

## Troubleshooting

### Server Won't Start

```bash
# Check container logs
docker compose logs manager

# Common fixes:
# 1. OpenSearch needs more virtual memory
sudo sysctl -w vm.max_map_count=262144
# Make permanent:
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# 2. Port already in use
sudo lsof -i :55000
sudo lsof -i :3000
```

### Agent Not Connecting

```bash
# 1. Test server is reachable from agent machine
curl http://<SERVER-IP>:55000/health

# 2. Check agent_config.json has correct server_url
cat /etc/cybersentinel/agent_config.json   # Linux
# or
Get-Content C:\ProgramData\CyberSentinel\agent_config.json   # Windows

# 3. Check agent logs
tail -f /var/log/cybersentinel_agent.log   # Linux
Get-Content C:\ProgramData\CyberSentinel\cybersentinel_agent.log -Tail 50   # Windows

# 4. Ensure firewall allows port 55000
sudo ufw allow 55000   # Ubuntu
```

### Dashboard Shows No Data

```bash
# 1. Check API is healthy
curl http://localhost:55000/ready

# 2. Check database has events
docker compose exec postgres psql -U dlp_user -d cybersentinel_dlp -c "SELECT COUNT(*) FROM events;"

# 3. Check OpenSearch
curl http://localhost:9200/_cat/indices
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Reduce OpenSearch heap (edit docker-compose.yml)
# Change: OPENSEARCH_JAVA_OPTS=-Xms256m -Xmx256m
# Then: docker compose down && docker compose up -d
```

### Reset Admin Password

```bash
docker compose exec manager python -c "
from app.core.security import get_password_hash
print(get_password_hash('NewPassword123!'))
"
# Use the hash to update directly:
docker compose exec postgres psql -U dlp_user -d cybersentinel_dlp -c \
  "UPDATE users SET hashed_password='<hash>' WHERE email='admin';"
```

---

## Technology Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| FastAPI | 0.104.1 | Async REST API framework |
| Uvicorn | 0.24.0 | ASGI server |
| SQLAlchemy | 2.0.23 | Async ORM (PostgreSQL) |
| Motor | 3.3.2 | Async MongoDB driver |
| Celery | 5.3.4 | Distributed task queue |
| Pydantic | 2.5.0 | Data validation |
| python-jose | 3.3.0 | JWT authentication |
| OpenSearch-py | 2.4.2 | Event search & analytics |
| Prometheus | 0.19.0 | Metrics collection |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18.2.0 | UI framework |
| TypeScript | 5.3.3 | Type safety |
| Vite | 5.0.8 | Build tool |
| TanStack Query | 5.14.2 | Server state management |
| Zustand | 4.4.7 | Client state |
| Recharts | 2.10.3 | Data visualization |
| Tailwind CSS | 3.3.6 | Styling |
| Axios | 1.6.2 | HTTP client |

### Infrastructure
| Technology | Version | Purpose |
|---|---|---|
| PostgreSQL | 15 | Users, policies, alerts |
| MongoDB | 7 | Event documents |
| Redis | 7 | Cache, sessions, broker |
| OpenSearch | 2.11 | Full-text search, analytics |
| Nginx | Alpine | Dashboard reverse proxy |
| Docker Compose | v2 | Container orchestration |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Clone the repo
git clone https://github.com/cybersentinel-06/Data-Loss-Prevention.git
cd Data-Loss-Prevention

# Install development dependencies
make install-dev

# Run tests
make test

# Lint and format
make lint
make format

# Run all CI checks locally
make ci-test
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

**Security Notice:** This is DLP (Data Loss Prevention) software. It monitors file access, clipboard operations, and USB devices. Ensure you have proper authorization before deploying in any environment.
