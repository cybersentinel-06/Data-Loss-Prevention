# CyberSentinel DLP - Current Codebase Analysis

**Analysis Date:** 2025-01-12
**Purpose:** Document existing code and plan refactoring to Wazuh-based architecture

---

## 📊 Current Project Structure

### Existing Directories
```
cybersentinel-dlp/
├── server/                     ✅ FastAPI backend (KEEP & REFACTOR)
├── dashboard/                  ⚠️ React dashboard (REBUILD)
├── agents/                     ⚠️ Agent code (REBUILD in Python)
├── database/                   ✅ DB initialization (KEEP)
├── config/                     ✅ Policy files (KEEP & EXPAND)
├── ml/                         ✅ ML models (KEEP)
├── policy-engine/              ✅ Policy evaluator (KEEP & ENHANCE)
├── integrations/               ✅ Wazuh forwarder (KEEP)
├── docker-compose.yml          ⚠️ Docker setup (REFACTOR)
└── Various docs/scripts        ✅ Documentation (UPDATE)
```

---

## ✅ What's Working (Can Reuse)

### 1. **Backend Core Structure** (`server/`)
**Status:** ✅ Good foundation, needs refactoring

**Existing Features:**
- FastAPI application with lifespan management
- Middleware: CORS, rate limiting, security headers, request ID
- Health check endpoints (`/health`, `/ready`)
- Exception handlers
- Structured logging (structlog)
- Prometheus metrics
- Database connections (PostgreSQL, MongoDB, Redis)

**Current API Endpoints:**
```python
✅ /api/v1/auth       # Authentication
✅ /api/v1/users      # User management
✅ /api/v1/agents     # Agent management
✅ /api/v1/events     # Event ingestion
✅ /api/v1/classification  # Classification
✅ /api/v1/policies   # Policy management
✅ /api/v1/alerts     # Alerts
✅ /api/v1/dashboard  # Dashboard data
```

**What Needs Change:**
- Change port from 8000 to 55000 (Wazuh standard)
- Add OpenSearch/Elasticsearch support
- Implement all 70+ API endpoints
- Add agent authentication (not just user auth)
- Implement full policy engine integration
- Add event correlation engine

### 2. **Database Layer**
**Status:** ✅ Working, needs enhancement

**Current Setup:**
- PostgreSQL 15: Users, configuration
- MongoDB 7: Events, agents, logs
- Redis 7: Cache, sessions, rate limiting

**Needs Addition:**
- OpenSearch/Elasticsearch for event indexing
- Implement daily rolling indices
- Add full-text search capabilities
- Retention policy implementation

### 3. **Policy Files** (`config/policies/`)
**Status:** ✅ Good YAML structure

**Existing Policies:**
- `gdpr-pii-protection.yaml`
- `hipaa-phi-protection.yaml`
- `pci-dss-credit-card.yaml`

**Example Structure:**
```yaml
policy:
  id: policy-pci-001
  name: "PCI-DSS Credit Card Protection"
  enabled: true
  severity: critical
  rules:
    - conditions:
        - field: content
          operator: regex
          value: '\b(?:\d{4}[\s-]?){3}\d{4}\b'
      actions:
        - type: alert
        - type: block
```

**What to Add:**
- More compliance templates
- Policy validation logic
- Policy testing framework
- Policy versioning

### 4. **Docker Compose**
**Status:** ⚠️ Needs refactoring

**Current Services:**
- ✅ PostgreSQL
- ✅ MongoDB
- ✅ Redis
- ✅ Server (FastAPI)
- ✅ Dashboard (Next.js)

**Missing:**
- OpenSearch/Elasticsearch
- Kibana/OpenSearch Dashboards (optional)
- Proper networking
- Volume management
- Health checks for all services

---

## ⚠️ What Needs Rebuilding

### 1. **Windows Agent** (`agents/endpoint/windows/` + `cybersentinel-dlp-agent-windows/`)
**Current:** C++ implementation
**Target:** Python implementation

**Current Capabilities:**
- File system monitoring (working)
- Clipboard monitoring (working)
- USB monitoring (working)
- Event reporting to server (working)

**Why Rebuild:**
- Easier maintenance with Python
- Cross-platform code sharing
- Faster development
- Better debugging

**New Architecture:**
```python
agents/
├── common/
│   ├── base_agent.py          # Base agent class
│   ├── monitors/
│   │   ├── file_monitor.py    # watchdog-based
│   │   ├── clipboard_monitor.py
│   │   ├── usb_monitor.py
│   │   └── network_monitor.py
│   └── communication.py       # HTTPS client
├── windows/
│   ├── agent.py               # Windows-specific agent
│   ├── service.py             # Windows service wrapper
│   └── install.ps1            # One-liner installer
└── linux/
    ├── agent.py               # Linux-specific agent
    ├── service.py             # systemd service
    └── install.sh             # One-liner installer
```

### 2. **Dashboard** (`dashboard/`)
**Current:** Next.js with basic UI
**Target:** Wazuh-style dashboard with full features

**Current Features:**
- Basic login
- Agent list (not working properly)
- Event list (incomplete)
- No KQL support
- No visualizations

**Required Features:**
```typescript
New Dashboard Components:
├── Overview Dashboard
│   ├── Real-time event stream (WebSocket)
│   ├── Event timeline chart (Recharts)
│   ├── Severity distribution (Pie chart)
│   ├── Top agents by events (Bar chart)
│   └── Quick stats (Cards)
│
├── Events & Logs Page
│   ├── KQL Search Bar (custom parser)
│   ├── Time range picker (last 15m, 1h, 24h, 7d, 30d, custom)
│   ├── Event table (virtualized for performance)
│   ├── Event details drawer
│   └── Export functionality (CSV, JSON)
│
├── Agents Management
│   ├── Agent list (status, last_seen, events_count)
│   ├── Agent details page
│   ├── Agent groups
│   ├── Configuration deployment
│   └── Bulk actions
│
├── Policy Management
│   ├── Policy list
│   ├── YAML editor with syntax highlighting
│   ├── Policy validation
│   ├── Policy testing
│   └── Policy templates
│
├── Incidents
│   ├── Incident list
│   ├── Incident workflow
│   ├── Assignment
│   └── Comments/notes
│
├── Visualizations
│   ├── Custom charts builder
│   ├── Graph library (Recharts/ApexCharts)
│   ├── Data export
│   └── Dashboard customization
│
└── Settings
    ├── User management
    ├── Integrations
    ├── System configuration
    └── API keys
```

---

## 🔧 Refactoring Plan

### Phase 1: Backend Refactoring (Week 1-2)

#### Task 1.1: Add OpenSearch Support
```python
server/app/core/opensearch.py
- OpenSearch client initialization
- Index template creation
- Daily rolling indices
- Query DSL builder
```

#### Task 1.2: Implement Core API Endpoints
```python
Priority endpoints (MVP):
✅ POST /v1/agents/register     # Agent auto-enrollment
✅ POST /v1/agents/auth         # Agent authentication
✅ GET  /v1/agents              # List agents
✅ GET  /v1/agents/{id}         # Agent details
✅ PATCH /v1/agents/{id}/status # Update status
✅ POST /v1/events              # Submit event
✅ POST /v1/events/batch        # Batch submit
✅ GET  /v1/events              # Query events (KQL)
✅ POST /v1/auth/login          # User login
✅ GET  /v1/system/health       # Health check
✅ POST /v1/policies            # Create policy
✅ GET  /v1/policies            # List policies
```

#### Task 1.3: Implement YAML Configuration
```yaml
/etc/cybersentinel/manager.yml
- Server configuration
- Database connections
- Authentication settings
- Agent enrollment settings
- Policy directory
- Logging configuration
```

#### Task 1.4: Build Event Processor Service
```python
server/app/services/event_processor.py
- Event validation
- Normalization
- Enrichment
- Classification
- Policy evaluation
- Alert generation
- Storage (OpenSearch)
```

#### Task 1.5: Build Policy Engine
```python
server/app/services/policy_engine.py
- Load policies from YAML
- Parse policy rules
- Evaluate events against policies
- Generate actions (alert, block, notify)
- Policy testing framework
```

### Phase 2: Agent Development (Week 3)

#### Task 2.1: Common Agent Framework
```python
agents/common/base_agent.py
- Agent base class
- Configuration loader (YAML)
- Server communication (HTTPS + JWT)
- Heartbeat management
- Event queue
- Retry logic
```

#### Task 2.2: Monitor Modules
```python
agents/common/monitors/
- file_monitor.py: watchdog/inotify
- clipboard_monitor.py: pyperclip/xclip
- usb_monitor.py: WMI/udev
- network_monitor.py: scapy (optional)
```

#### Task 2.3: Windows Agent
```python
agents/windows/
- agent.py: Main Windows agent
- service.py: Windows service wrapper (using pythonservice/nssm)
- install.ps1: One-liner PowerShell installer
- config.yml.template: Configuration template
```

#### Task 2.4: Linux Agent
```python
agents/linux/
- agent.py: Main Linux agent
- service.py: systemd service wrapper
- install.sh: One-liner bash installer
- config.yml.template: Configuration template
```

### Phase 3: Dashboard Development (Week 4)

#### Task 3.1: Project Setup
```bash
dashboard/
- React 18 + TypeScript
- Vite for build tooling
- Material-UI or Ant Design
- Redux Toolkit for state
- React Router for routing
- Recharts/ApexCharts for visualizations
```

#### Task 3.2: Core Components
```typescript
src/components/
- Layout (header, sidebar, content)
- Authentication (login, logout)
- Common components (tables, cards, modals)
```

#### Task 3.3: KQL Parser Implementation
```typescript
src/utils/kqlParser.ts
- Lexer: Tokenize KQL query
- Parser: Build AST
- Translator: Convert to OpenSearch Query DSL
- Support: field:value, AND, OR, NOT, >, <, >=, <=, wildcards
```

#### Task 3.4: Visualization Components
```typescript
src/components/Visualizations/
- LineChart.tsx (time series)
- BarChart.tsx (top N)
- PieChart.tsx (distribution)
- HeatMap.tsx (correlation)
- Gauge.tsx (metrics)
```

### Phase 4: Integration & Testing (Week 5)

#### Task 4.1: Unit Tests
```python
manager/tests/unit/
- test_api_endpoints.py
- test_event_processor.py
- test_policy_engine.py
- test_kql_parser.py (TypeScript)
```

#### Task 4.2: Integration Tests
```python
manager/tests/integration/
- test_database_integration.py
- test_event_pipeline.py
- test_agent_communication.py
```

#### Task 4.3: E2E Tests
```typescript
dashboard/tests/e2e/
- test_login_flow.spec.ts
- test_agent_management.spec.ts
- test_event_search.spec.ts
```

### Phase 5: Documentation & Deployment (Week 6)

#### Task 5.1: Documentation
```markdown
docs/
├── installation/
│   ├── server.md (Ubuntu Docker Compose install)
│   ├── windows-agent.md (One-liner PowerShell)
│   └── linux-agent.md (One-liner bash)
├── api/
│   └── api-reference.md (All 70+ endpoints)
├── user-guide/
│   ├── getting-started.md
│   ├── kql-guide.md
│   └── policy-creation.md
└── development/
    ├── contributing.md
    └── architecture.md
```

#### Task 5.2: Docker Compose Refactoring
```yaml
docker-compose.yml (Production-ready)
- OpenSearch
- PostgreSQL
- MongoDB
- Redis
- Manager (FastAPI on port 55000)
- Dashboard (React on port 3000)
- Proper networking
- Volume persistence
- Health checks
- Resource limits
```

#### Task 5.3: CI/CD Setup
```yaml
.github/workflows/
- ci.yml: Lint, test, build
- release.yml: Docker image build/push
- docs.yml: Documentation deployment
```

---

## 📋 File-by-File Reuse Decision

### Keep & Refactor (✅)
```
server/app/main.py              ✅ Core FastAPI setup
server/app/core/database.py     ✅ DB connections (add OpenSearch)
server/app/core/security.py     ✅ Auth logic
server/app/core/config.py       ✅ Config loader (add YAML support)
server/app/api/v1/*.py          ✅ API endpoints (extend)
server/app/models/*.py          ✅ Data models (update)
config/policies/*.yaml          ✅ Policy templates
docker-compose.yml              ✅ Infrastructure (refactor)
```

### Rebuild (🔄)
```
dashboard/*                     🔄 Complete rebuild (Wazuh-style)
agents/endpoint/*               🔄 Rewrite in Python
cybersentinel-dlp-agent-windows/* 🔄 Rewrite in Python
```

### Remove (❌)
```
*.tmp files                     ❌ Remove
Old test scripts                ❌ Remove
Duplicate directories           ❌ Consolidate
```

---

## 🎯 Success Metrics

**MVP Complete When:**
- [x] Architecture document created
- [ ] All Phase 1 tasks complete (backend)
- [ ] All Phase 2 tasks complete (agents)
- [ ] All Phase 3 tasks complete (dashboard)
- [ ] All Phase 4 tasks complete (testing)
- [ ] All Phase 5 tasks complete (docs/deploy)
- [ ] One-liner installers working
- [ ] KQL search functional
- [ ] Visualizations rendering
- [ ] 80%+ test coverage
- [ ] Complete documentation
- [ ] GitHub org created with repos

---

**Next Steps:**
1. Complete this analysis
2. Start Phase 1: Backend refactoring
3. Implement core API endpoints
4. Add OpenSearch support
5. Build event processor
6. Continue with agents...

---

**Document Version:** 1.0
**Last Updated:** 2025-01-12
