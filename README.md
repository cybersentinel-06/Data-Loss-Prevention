# CyberSentinel DLP - Enterprise Data Loss Prevention Platform

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)

## Overview

CyberSentinel DLP is a production-ready, enterprise-grade Data Loss Prevention platform designed to protect sensitive data across endpoints, networks, and cloud environments. Built with scalability, security, and compliance at its core.

## Key Features

- **Multi-Layer Protection**: Endpoint agents, network collectors, and cloud connectors
- **Advanced Detection**: Hybrid classification using regex, fingerprinting, entropy analysis, and ML/NLP
- **Flexible Policy Engine**: YAML-based policy DSL with complex rule logic
- **Real-Time Enforcement**: Block, redact, encrypt, and quarantine capabilities
- **Compliance Ready**: GDPR, HIPAA, PCI-DSS, SOX, PHI, PI compliance built-in
- **SIEM Integration**: Native Wazuh integration with custom decoders
- **Modern Dashboard**: Beautiful Next.js UI accessible via host IP
- **Production-Ready**: High availability, scalability, monitoring, and audit logging

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Dashboard                        │
│              (Real-time Monitoring & Management)             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Server                    │
│           (Authentication, API Gateway, Business Logic)      │
└─┬──────────────┬──────────────┬──────────────┬─────────────┘
  │              │              │              │
  ▼              ▼              ▼              ▼
┌────────┐  ┌─────────┐  ┌──────────┐  ┌──────────────┐
│Endpoint│  │ Network │  │  Cloud   │  │Policy Engine │
│ Agents │  │Collectors│  │Connectors│  │& ML Classifier│
└────────┘  └─────────┘  └──────────┘  └──────────────┘
     │            │            │              │
     └────────────┴────────────┴──────────────┘
                    │
                    ▼
     ┌─────────────────────────────┐
     │  Hybrid Database Layer      │
     │  PostgreSQL + MongoDB       │
     └──────────────┬──────────────┘
                    │
                    ▼
     ┌─────────────────────────────┐
     │    Wazuh SIEM Integration   │
     │   (Alerts, Monitoring, SOC) │
     └─────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- MongoDB 7+
- Docker & Docker Compose (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourorg/cybersentinel-dlp.git
cd cybersentinel-dlp

# Install backend dependencies
cd server
pip install -r requirements.txt

# Install dashboard dependencies
cd ../dashboard
npm install

# Set up environment variables
cp config/env-templates/.env.server.example server/.env
cp config/env-templates/.env.dashboard.example dashboard/.env.local

# Run database migrations
cd ../server
alembic upgrade head

# Start the services
cd ..
docker-compose up -d
```

### Access the Dashboard

Open your browser and navigate to:
```
http://<your-host-ip>:3000
```

Default credentials:
- Username: `admin@cybersentinel.local`
- Password: `ChangeMe123!`

## Module Documentation

Each module has comprehensive documentation in its respective directory:

- **[Server](docs/modules/SERVER.md)** - FastAPI backend server
- **[Database](docs/modules/DATABASE.md)** - PostgreSQL + MongoDB setup
- **[Dashboard](docs/modules/DASHBOARD.md)** - Next.js frontend
- **[Endpoint Agents](docs/modules/AGENTS.md)** - Cross-platform agents
- **[Network Collectors](docs/modules/COLLECTORS.md)** - Protocol parsers
- **[Cloud Connectors](docs/modules/CONNECTORS.md)** - Cloud integrations
- **[ML Classifiers](docs/modules/ML.md)** - Machine learning pipeline
- **[Policy Engine](docs/modules/POLICY_ENGINE.md)** - Rule evaluation
- **[Wazuh Integration](docs/modules/WAZUH.md)** - SIEM integration

## Master Documentation

For complete system documentation, see **[MASTER_DOCUMENTATION.md](MASTER_DOCUMENTATION.md)**

## Project Structure

```
cybersentinel-dlp/
├── server/                 # FastAPI backend
├── database/              # Database schemas and migrations
├── dashboard/             # Next.js frontend
├── agents/                # Endpoint agents
├── collectors/            # Network collectors
├── connectors/            # Cloud connectors
├── ml/                    # ML training and inference
├── policy-engine/         # Policy evaluation engine
├── integrations/          # SIEM integrations
├── infrastructure/        # Docker, K8s, Terraform
├── config/                # Configuration templates
└── docs/                  # Documentation
```

## Compliance

CyberSentinel DLP is designed to help organizations meet compliance requirements for:

- **GDPR** - General Data Protection Regulation
- **HIPAA** - Health Insurance Portability and Accountability Act
- **PCI-DSS** - Payment Card Industry Data Security Standard
- **SOX** - Sarbanes-Oxley Act
- **PHI** - Protected Health Information
- **PI** - Personal Information

See [Compliance Documentation](docs/compliance/COMPLIANCE.md) for details.

## Performance Targets

- **Detection Precision**: ≥ 0.90
- **Detection Recall**: ≥ 0.85
- **Mean Time to Detect**: < 5 minutes
- **False Positive Rate**: < 3%
- **Classification Latency**: < 300ms
- **System Availability**: 99.9%

## Security

- **Authentication**: JWT + OAuth2 + mTLS
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **RBAC**: Fine-grained role-based access control
- **Audit Logging**: Immutable audit trail
- **Secrets Management**: HashiCorp Vault integration

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/yourorg/cybersentinel-dlp/issues)
- Email: support@cybersentinel.local

## Roadmap

- [ ] Advanced ML models (BERT, transformers)
- [ ] Kubernetes Operator
- [ ] Mobile device support
- [ ] Advanced OCR for images
- [ ] Real-time collaboration features
- [ ] Multi-tenancy support

---

**Built with ❤️ by the CyberSentinel Team**
