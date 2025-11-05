#!/bin/bash

# ============================================================================
# CyberSentinel DLP - GitHub Upload Script
# ============================================================================
# This script automates the process of uploading to GitHub
# Repository: https://github.com/effaaykhan/cybersentinel-dlp
# ============================================================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  CyberSentinel DLP - GitHub Upload${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}Error: Git is not installed!${NC}"
    echo "Please install Git first: https://git-scm.com/downloads"
    exit 1
fi

echo -e "${GREEN}✓ Git is installed${NC}"

# Navigate to project directory
cd "$(dirname "$0")"

echo -e "${BLUE}Current directory: $(pwd)${NC}"
echo ""

# Check if already initialized
if [ -d ".git" ]; then
    echo -e "${YELLOW}Git repository already initialized${NC}"
else
    echo -e "${BLUE}Initializing Git repository...${NC}"
    git init
    echo -e "${GREEN}✓ Git repository initialized${NC}"
fi

# Configure git user (update with your details)
echo -e "${BLUE}Configuring Git user...${NC}"
git config user.name "effaaykhan"
read -p "Enter your email: " USER_EMAIL
git config user.email "$USER_EMAIL"
echo -e "${GREEN}✓ Git configured${NC}"
echo ""

# Add all files
echo -e "${BLUE}Adding files to git...${NC}"
git add .
echo -e "${GREEN}✓ Files added${NC}"

# Create commit
echo -e "${BLUE}Creating commit...${NC}"
git commit -m "Initial commit: CyberSentinel DLP Platform

Features:
- Complete FastAPI backend with real database queries
- Next.js dashboard with API integration
- Docker Compose orchestration (5 services)
- Systemd service files for production deployment
- Automated deployment scripts for Ubuntu
- Comprehensive documentation
- Support for Windows and Linux agents
- GDPR, HIPAA, PCI-DSS compliance ready
- Real-time DLP monitoring and classification
- Wazuh SIEM integration

Tech Stack:
- Backend: Python 3.11 + FastAPI
- Frontend: Next.js 14 + TypeScript
- Databases: PostgreSQL 15 + MongoDB 7 + Redis 7
- Deployment: Docker + Docker Compose + Systemd
- Security: JWT auth, RBAC, rate limiting, encryption"

echo -e "${GREEN}✓ Commit created${NC}"
echo ""

# Add remote repository
echo -e "${BLUE}Adding remote repository...${NC}"
if git remote | grep -q "origin"; then
    echo -e "${YELLOW}Remote 'origin' already exists, removing...${NC}"
    git remote remove origin
fi

git remote add origin https://github.com/effaaykhan/cybersentinel-dlp.git
echo -e "${GREEN}✓ Remote added${NC}"
echo ""

# Rename branch to main
echo -e "${BLUE}Renaming branch to main...${NC}"
git branch -M main
echo -e "${GREEN}✓ Branch renamed${NC}"
echo ""

# Push to GitHub
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Ready to push to GitHub!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT:${NC}"
echo "When prompted for credentials:"
echo "  Username: effaaykhan"
echo "  Password: [Your GitHub Personal Access Token]"
echo ""
echo "Don't have a token? Generate one at:"
echo "  https://github.com/settings/tokens"
echo ""
read -p "Press Enter to push to GitHub..."

git push -u origin main

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  ✅ Successfully uploaded to GitHub!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Repository URL:"
echo "  https://github.com/effaaykhan/cybersentinel-dlp"
echo ""
echo "Clone command:"
echo "  git clone https://github.com/effaaykhan/cybersentinel-dlp.git"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Visit your repository on GitHub"
echo "  2. Add description and topics"
echo "  3. Enable Issues and Wiki"
echo "  4. Create a release (v1.0.0)"
echo "  5. Share with your team!"
echo ""
