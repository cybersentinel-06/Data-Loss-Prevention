# CyberSentinel DLP - Architecture & Implementation Plan

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      CyberSentinel DLP Platform                  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────────────────────┐
│  Windows Agent   │────────▶│                                   │
│  (Python 3.10+)  │         │      Server (Ubuntu 22.04/24.04)  │
└──────────────────┘         │                                   │
                             │  ┌─────────────────────────────┐  │
┌──────────────────┐         │  │   FastAPI Backend           │  │
│   Linux Agent    │────────▶│  │   (Python 3.11)             │  │
│  (Python 3.10+)  │         │  │   Port: 8000                │  │
└──────────────────┘         │  └─────────────────────────────┘  │
                             │                                   │
                             │  ┌─────────────────────────────┐  │
                             │  │   React Dashboard           │  │
                             │  │   (Node.js 20 LTS)          │  │
     ┌──────────────┐        │  │   Port: 3000                │  │
     │   Browser    │───────▶│  └─────────────────────────────┘  │
     └──────────────┘        │                                   │
                             │  ┌──────┬──────────┬──────────┐  │
                             │  │ PG   │ MongoDB  │  Redis   │  │
                             │  │:5432 │  :27017  │  :6379   │  │
                             │  └──────┴──────────┴──────────┘  │
                             └──────────────────────────────────┘
```

## Technology Stack (Tested Versions)

### Server Components
- **OS**: Ubuntu 22.04 LTS / 24.04 LTS
- **Container**: Docker 24.0.7, Docker Compose 2.23.0
- **Backend**: Python 3.11.6, FastAPI 0.104.1
- **Frontend**: Node.js 20.10.0 LTS, React 18.2.0
- **Databases**:
  - PostgreSQL 15.5 (users, authentication)
  - MongoDB 7.0.4 (events, agents, logs)
  - Redis 7.2.3 (cache, sessions)

### Agent Components
- **Python**: 3.10+ (Windows/Linux compatible)
- **Config**: PyYAML 6.0.1
- **Monitoring**: Watchdog 3.0.0
- **HTTP**: Requests 2.31.0
- **Windows Specific**: pywin32 306, WMI 1.5.1

## Directory Structure

### Server Repository (`cybersentinel-dlp-server`)
```
cybersentinel-dlp-server/
├── install.sh                    # One-line installer for Ubuntu
├── uninstall.sh                  # Uninstallation script
├── docker-compose.yml            # Main deployment config
├── .env.example                  # Environment template
├── README.md                     # Installation guide
├── UNINSTALL.md                  # Uninstallation guide
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration loader
│   │   ├── api/
│   │   │   ├── agents.py        # Agent management API
│   │   │   ├── events.py        # Events API
│   │   │   ├── auth.py          # Authentication API
│   │   │   ├── policies.py      # Policy management
│   │   │   └── analytics.py     # Dashboard analytics
│   │   ├── models/
│   │   ├── services/
│   │   └── core/
│   │       ├── database.py      # DB connections
│   │       ├── security.py      # Auth/JWT
│   │       └── agent_enrollment.py  # Auto-enrollment
│   └── init_db.py               # Database initialization
│
├── dashboard/
│   ├── Dockerfile
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── App.js
│       ├── components/
│       │   ├── Dashboard/       # Main dashboard with charts
│       │   ├── Agents/          # Agents management
│       │   ├── Events/          # Events with KQL search
│       │   ├── Policies/        # Policy configuration
│       │   └── Settings/        # System settings
│       ├── services/
│       │   └── api.js           # API client
│       └── utils/
│           └── kql.js           # KQL parser
│
├── config/
│   ├── server.yml               # Server configuration template
│   └── policies/
│       ├── default.yml          # Default DLP policies
│       ├── pci-dss.yml          # PCI-DSS compliance
│       ├── gdpr.yml             # GDPR compliance
│       └── hipaa.yml            # HIPAA compliance
│
└── docs/
    ├── API.md                   # API documentation
    ├── DEPLOYMENT.md            # Deployment guide
    └── TROUBLESHOOTING.md       # Common issues
```

### Windows Agent Repository (`cybersentinel-dlp-agent-windows`)
```
cybersentinel-dlp-agent-windows/
├── install.ps1                  # PowerShell installer (one-liner compatible)
├── uninstall.ps1                # Uninstallation script
├── README.md                    # Installation guide
├── requirements.txt             # Python dependencies
├── agent.py                     # Main agent code
├── config/
│   └── agent.yml.template       # YAML config template
└── service/
    └── install_service.ps1      # Service installation helper
```

### Linux Agent Repository (`cybersentinel-dlp-agent-linux`)
```
cybersentinel-dlp-agent-linux/
├── install.sh                   # Bash installer (one-liner compatible)
├── uninstall.sh                 # Uninstallation script
├── README.md                    # Installation guide
├── requirements.txt             # Python dependencies
├── agent.py                     # Main agent code
├── config/
│   └── agent.yml.template       # YAML config template
└── service/
    ├── cybersentinel-agent.service  # Systemd service file
    └── install_service.sh       # Service installation helper
```

## Installation Flows

### Server Installation
```bash
# Ubuntu 22.04 or 24.04
curl -sSL https://raw.githubusercontent.com/effaaykhan/cybersentinel-dlp-server/main/install.sh | bash

# Output at end:
# ✅ CyberSentinel DLP Server installed successfully!
#
# Dashboard URL: http://YOUR_IP:3000
# Username: admin
# Password: admin
#
# IMPORTANT: Change the default password after first login!
```

### Windows Agent Installation
```powershell
# PowerShell (Administrator)
iwr -useb https://raw.githubusercontent.com/effaaykhan/cybersentinel-dlp-agent-windows/main/install.ps1 | iex

# Prompts for:
# - Server IP address
# Then auto-registers as AGENT-001, AGENT-002, etc.
```

### Linux Agent Installation
```bash
curl -sSL https://raw.githubusercontent.com/effaaykhan/cybersentinel-dlp-agent-linux/main/install.sh | bash

# Prompts for:
# - Server IP address
# Then auto-registers as AGENT-001, AGENT-002, etc.
```

## Configuration Files

### Server Config (`/etc/cybersentinel/server.yml`)
```yaml
server:
  host: 0.0.0.0
  port: 8000
  environment: production
  secret_key: ${SECRET_KEY}

databases:
  postgresql:
    host: localhost
    port: 5432
    database: cybersentinel_dlp
    user: dlp_user
    password: ${POSTGRES_PASSWORD}

  mongodb:
    host: localhost
    port: 27017
    database: cybersentinel_dlp
    user: dlp_user
    password: ${MONGODB_PASSWORD}

  redis:
    host: localhost
    port: 6379
    password: ${REDIS_PASSWORD}

auth:
  jwt_secret: ${JWT_SECRET}
  access_token_expire: 30  # minutes
  refresh_token_expire: 7  # days

agent_enrollment:
  auto_approve: true
  id_prefix: "AGENT"
  id_start: 1
  require_auth_key: false

dashboard:
  default_username: admin
  default_password: admin  # Changed on first login
```

### Agent Config (Windows: `C:\Program Files\CyberSentinel\agent.yml`)
### Agent Config (Linux: `/etc/cybersentinel/agent.yml`)
```yaml
agent:
  id: ""  # Auto-assigned by server
  name: "${HOSTNAME}"
  server_url: "http://SERVER_IP:8000/api/v1"

monitoring:
  file_system:
    enabled: true
    paths:
      - "C:\\Users\\Public\\Documents"      # Windows
      - "C:\\Users\\${USERNAME}\\Desktop"
      - "C:\\Users\\${USERNAME}\\Documents"
      # OR for Linux:
      # - "/home"
      # - "/var/www"
    extensions:
      - .pdf
      - .docx
      - .xlsx
      - .txt
      - .csv

  clipboard:
    enabled: true  # Windows only

  usb:
    enabled: true

classification:
  enabled: true
  max_file_size_mb: 10
  patterns:
    - type: credit_card
      regex: '\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
      severity: critical
    - type: ssn
      regex: '\b\d{3}-\d{2}-\d{4}\b'
      severity: critical
    - type: email
      regex: '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
      severity: medium

reporting:
  heartbeat_interval: 60  # seconds
  batch_events: false
  retry_attempts: 3
```

## API Endpoints

### Agent Management
- `POST /api/v1/agents/enroll` - Auto-enrollment (no auth required)
- `GET /api/v1/agents` - List all agents
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `POST /api/v1/agents/{agent_id}/heartbeat` - Agent heartbeat
- `PUT /api/v1/agents/{agent_id}` - Update agent
- `DELETE /api/v1/agents/{agent_id}` - Remove agent

### Events
- `POST /api/v1/events` - Submit event (from agent)
- `GET /api/v1/events` - Query events (supports KQL)
- `GET /api/v1/events/{event_id}` - Get event details
- `GET /api/v1/events/analytics` - Analytics for dashboard

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/change-password` - Change password

### Policies
- `GET /api/v1/policies` - List policies
- `POST /api/v1/policies` - Create policy
- `PUT /api/v1/policies/{id}` - Update policy
- `DELETE /api/v1/policies/{id}` - Delete policy

## Dashboard Features (Wazuh-Style)

### 1. Overview Dashboard
- **Real-time Event Stream** - Last 100 events, auto-refresh
- **Top 10 Agents by Events** - Bar chart
- **Events by Severity** - Pie chart (Low, Medium, High, Critical)
- **Events Timeline** - Line graph (last 24 hours)
- **Events by Type** - Bar chart (File, Clipboard, USB)
- **Geographic Map** - Agent locations (if IP geolocation enabled)

### 2. Agents Page
- **Agent List** - Table with status, last seen, events count
- **Agent Details** - Click to see full details
- **Agent Groups** - Group agents for policy management
- **Bulk Actions** - Deploy policies, restart, remove

### 3. Events Page
- **KQL Search Bar** - `event_type:"file" AND severity:"critical"`
- **Time Range Selector** - Last 15m, 1h, 24h, 7d, 30d, Custom
- **Filters** - Agent, Type, Severity, User
- **Event Details** - Expandable rows with full event data
- **Export** - CSV, JSON export

### 4. Policies Page
- **Policy Templates** - GDPR, HIPAA, PCI-DSS, Custom
- **Policy Editor** - YAML editor with validation
- **Agent Assignment** - Assign policies to agents/groups
- **Policy Testing** - Test policy on sample data

### 5. Settings
- **User Management** - Add/remove users, change passwords
- **System Configuration** - Server settings, database config
- **API Keys** - Generate API keys for integrations

## Agent Auto-Enrollment Process

1. Agent starts, reads config (`agent.yml`)
2. If `agent.id` is empty:
   - Agent sends enrollment request to `/api/v1/agents/enroll`
   - Payload: `{hostname, os, ip_address, capabilities}`
3. Server receives enrollment:
   - Generates next available ID (AGENT-001, AGENT-002, etc.)
   - Creates agent record in MongoDB
   - Returns assigned `agent_id` to agent
4. Agent saves `agent_id` to config file
5. Agent appears immediately in dashboard

## Event Correlation & KQL

### KQL Query Examples
```
# Find critical file events from specific agent
event_type:"file" AND severity:"critical" AND agent_id:"AGENT-001"

# Find USB events in last hour
event_type:"usb" AND timestamp > now-1h

# Find multiple credit card detections
classification.labels:"PAN" AND count > 5
```

### Correlation Rules
```yaml
# Example: Detect data exfiltration
name: "Potential Data Exfiltration"
rule:
  - event_type: "usb"
    event_subtype: "usb_connected"
  - event_type: "file"
    event_subtype: "file_copied"
    within: 300  # 5 minutes
    same_user: true
action: alert
severity: critical
```

## Security

### Authentication
- JWT tokens (access + refresh)
- Password hashing (bcrypt)
- Rate limiting (Redis)
- Session management

### Agent Communication
- HTTPS recommended (optional cert config)
- Agent authentication via agent_id
- Optional API key authentication

### Data Protection
- Sensitive data redaction in logs
- File quarantine for critical events
- Encryption at rest (MongoDB encryption)

## Uninstallation Options

### Option 1: Keep Data
```bash
# Server
sudo /opt/cybersentinel/uninstall.sh --keep-data

# Agent (Windows)
.\uninstall.ps1 -KeepData

# Agent (Linux)
sudo /opt/cybersentinel/uninstall.sh --keep-data
```

### Option 2: Complete Removal
```bash
# Server
sudo /opt/cybersentinel/uninstall.sh --purge

# Agent (Windows)
.\uninstall.ps1 -Purge

# Agent (Linux)
sudo /opt/cybersentinel/uninstall.sh --purge
```

## Testing Plan

### Server Testing
1. Test on Ubuntu 22.04 VM
2. Test on Ubuntu 24.04 VM
3. Verify all services start
4. Verify dashboard accessible
5. Test login with admin:admin
6. Test password change

### Agent Testing
1. Test Windows agent on Windows 10/11
2. Test Linux agent on Ubuntu 22.04/24.04
3. Verify auto-enrollment
4. Verify events appear in dashboard
5. Test all monitoring features

## Documentation Requirements

### For Each Repository
- `README.md` - Quick start, installation
- `INSTALL.md` - Detailed installation guide
- `UNINSTALL.md` - Uninstallation guide
- `CONFIGURATION.md` - Configuration reference
- `TROUBLESHOOTING.md` - Common issues
- `API.md` - API documentation (server only)

### Version Documentation
All documentation must include:
- Tested OS versions
- Required software versions
- Python package versions
- Docker/Node.js versions

## Implementation Order

1. ✅ Architecture design (this document)
2. Backend API (FastAPI)
3. Database initialization
4. Agent enrollment system
5. React Dashboard
6. Windows Agent (Python)
7. Linux Agent (Python)
8. Installation scripts
9. Uninstallation scripts
10. Testing on Ubuntu 22.04/24.04
11. Documentation
12. GitHub push

---

**Status**: Architecture Complete - Ready for Implementation
**Next**: Start building backend API
