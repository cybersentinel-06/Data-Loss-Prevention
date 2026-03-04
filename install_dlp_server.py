#!/usr/bin/env python3
"""
CyberSentinel DLP Server - Remote Installer

Downloads docker-compose.deploy.yml, .env.example, and the DB init script
from GitHub, generates .env with random secrets, and runs docker compose up -d.
No source code or build step needed — all images are pre-built on GHCR.

Usage:
    python3 install_dlp_server.py                      # Install to ./cybersentinel-dlp and start
    python3 install_dlp_server.py /opt/dlp             # Install to custom path
    python3 install_dlp_server.py --no-start           # Download & configure only, don't start
"""

import argparse
import os
import platform
import secrets
import shutil
import socket
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

REPO_OWNER = "cybersentinel-06"
REPO_NAME = "Data-Loss-Prevention"
DEFAULT_BRANCH = "main"
DEFAULT_INSTALL_DIR = "cybersentinel-dlp"

# Raw GitHub URL base
RAW_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}"

# Files to download:  (remote_path, local_path)
FILES = [
    ("docker-compose.deploy.yml", "docker-compose.yml"),
    (".env.example", ".env.example"),
    ("database/postgresql/init/01-init.sql", "init-scripts/01-init.sql"),
]


# ──────────────────────────────────────────────
# Terminal colours
# ──────────────────────────────────────────────

class Color:
    if sys.stdout.isatty():
        BOLD = "\033[1m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        CYAN = "\033[96m"
        RESET = "\033[0m"
    else:
        BOLD = GREEN = YELLOW = RED = CYAN = RESET = ""


def info(msg):
    print(f"  {Color.CYAN}[INFO]{Color.RESET}  {msg}")


def ok(msg):
    print(f"  {Color.GREEN}[ OK ]{Color.RESET}  {msg}")


def warn(msg):
    print(f"  {Color.YELLOW}[WARN]{Color.RESET}  {msg}")


def err(msg):
    print(f"  {Color.RED}[FAIL]{Color.RESET}  {msg}")


def banner():
    print(
        textwrap.dedent(f"""\
    {Color.CYAN}{Color.BOLD}
    ╔══════════════════════════════════════════════════╗
    ║       CyberSentinel DLP  -  Server Installer    ║
    ╚══════════════════════════════════════════════════╝{Color.RESET}
    """)
    )


# ──────────────────────────────────────────────
# Prerequisite checks
# ──────────────────────────────────────────────

def check_prerequisites():
    """Verify Docker daemon is running and Docker Compose is available."""
    print(f"\n{Color.BOLD}[1/4] Checking prerequisites{Color.RESET}\n")
    all_ok = True

    # Python version
    if sys.version_info >= (3, 8):
        ok(f"Python {platform.python_version()}")
    else:
        err(f"Python >= 3.8 required (found {platform.python_version()})")
        all_ok = False

    # Docker binary
    if not shutil.which("docker"):
        err("Docker not found. Install: https://docs.docker.com/engine/install/")
        all_ok = False
    else:
        try:
            ver = subprocess.check_output(
                ["docker", "--version"], stderr=subprocess.DEVNULL, text=True
            ).strip()
            ok(f"Docker found  ({ver})")
        except subprocess.CalledProcessError:
            ok("Docker found")

        # Docker daemon must be running (docker info talks to the daemon)
        result = subprocess.run(
            ["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if result.returncode != 0:
            err("Docker daemon is not running!")
            info("Start it with:  sudo systemctl start docker")
            all_ok = False
        else:
            ok("Docker daemon is running")

    # Docker Compose — prefer v2 plugin, skip legacy v1 entirely
    compose_cmd = None
    try:
        subprocess.check_output(
            ["docker", "compose", "version"], stderr=subprocess.DEVNULL, text=True
        )
        compose_cmd = ["docker", "compose"]
        ok("Docker Compose v2 found  (docker compose)")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # v2 plugin not available — check standalone docker-compose
        if shutil.which("docker-compose"):
            try:
                ver_out = subprocess.check_output(
                    ["docker-compose", "--version"], stderr=subprocess.DEVNULL, text=True
                ).strip()
                # docker-compose v1 (Python) reports "docker-compose version 1.x.x"
                # docker-compose v2 standalone reports "Docker Compose version v2.x.x"
                if "version 1." in ver_out.lower() or "1.29" in ver_out:
                    warn(f"Found legacy docker-compose v1 ({ver_out})")
                    err("docker-compose v1 is deprecated and unsupported.")
                    info("Install Docker Compose v2: https://docs.docker.com/compose/install/")
                else:
                    compose_cmd = ["docker-compose"]
                    ok(f"Docker Compose found  ({ver_out})")
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

    if compose_cmd is None and all_ok:
        err("Docker Compose v2 not found.")
        info("Install: https://docs.docker.com/compose/install/")
        all_ok = False

    if not all_ok:
        print()
        err("Please fix the issues above and re-run the installer.")
        sys.exit(1)

    return compose_cmd


# ──────────────────────────────────────────────
# Download files
# ──────────────────────────────────────────────

def download_file(url, dest):
    """Download a single file from *url* to *dest*."""
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except urllib.error.HTTPError as exc:
        err(f"HTTP {exc.code} downloading {url}")
        return False
    except urllib.error.URLError as exc:
        err(f"Network error: {exc.reason}")
        return False


def download_all(install_dir, branch):
    """Download all required files into *install_dir*."""
    print(f"\n{Color.BOLD}[2/4] Downloading deployment files{Color.RESET}\n")
    os.makedirs(install_dir, exist_ok=True)

    for remote_path, local_path in FILES:
        url = f"{RAW_BASE}/{branch}/{remote_path}"
        dest = os.path.join(install_dir, local_path)
        if download_file(url, dest):
            ok(f"  {local_path}")
        else:
            err(f"  Failed to download {remote_path}")
            sys.exit(1)

    ok(f"All files saved to {os.path.abspath(install_dir)}/")


# ──────────────────────────────────────────────
# Environment configuration
# ──────────────────────────────────────────────

def detect_host_ip():
    """Best-effort detection of the machine's LAN IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def generate_env(install_dir):
    """Generate a production .env from .env.example with random secrets."""
    print(f"\n{Color.BOLD}[3/4] Generating environment configuration{Color.RESET}\n")

    example = os.path.join(install_dir, ".env.example")
    env_file = os.path.join(install_dir, ".env")

    if os.path.exists(env_file):
        warn(".env already exists — skipping generation (keeping existing config)")
        return

    host_ip = detect_host_ip()
    info(f"Detected host IP: {host_ip}")

    # Generate strong random secrets
    secret_key = secrets.token_hex(32)
    pg_pass = secrets.token_hex(16)
    mongo_pass = secrets.token_hex(16)
    redis_pass = secrets.token_hex(16)

    with open(example, "r") as f:
        content = f.read()

    replacements = {
        "change-this-to-a-random-secret-key-min-32-chars": secret_key,
        "change-this-strong-postgres-password": pg_pass,
        "change-this-strong-mongodb-password": mongo_pass,
        "change-this-strong-redis-password": redis_pass,
        "your-ubuntu-server-ip": host_ip,
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    with open(env_file, "w") as f:
        f.write(content)

    os.chmod(env_file, 0o600)
    ok(f".env generated with random secrets (permissions: 600)")
    ok(f"Dashboard URL:  http://{host_ip}:3000")
    ok(f"API URL:        http://{host_ip}:55000")


# ──────────────────────────────────────────────
# Start services
# ──────────────────────────────────────────────

def docker_up(install_dir, compose_cmd):
    """Pull images and start services."""
    print(f"\n{Color.BOLD}[4/4] Pulling images and starting services{Color.RESET}\n")
    info("Pulling pre-built images from ghcr.io (this may take a few minutes) ...")

    result = subprocess.run(compose_cmd + ["pull"], cwd=install_dir)
    if result.returncode != 0:
        err("Failed to pull images. Check Docker login / network.")
        sys.exit(1)
    ok("All images pulled")

    info("Starting services ...")
    result = subprocess.run(compose_cmd + ["up", "-d"], cwd=install_dir)
    if result.returncode != 0:
        err("Failed to start services. Check the output above for details.")
        sys.exit(1)
    ok("All services started")


# ──────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────

def print_summary(install_dir, host_ip, started):
    abs_path = os.path.abspath(install_dir)
    status = f"{Color.GREEN}Running{Color.RESET}" if started else f"{Color.YELLOW}Not started{Color.RESET}"

    print(
        textwrap.dedent(f"""
    {Color.CYAN}{Color.BOLD}
    ╔══════════════════════════════════════════════════╗
    ║          Installation Complete                   ║
    ╚══════════════════════════════════════════════════╝{Color.RESET}

    {Color.BOLD}Install path:{Color.RESET}  {abs_path}
    {Color.BOLD}Services:    {Color.RESET}  {status}

    {Color.BOLD}Endpoints:{Color.RESET}
      Dashboard   →  http://{host_ip}:3000
      API Server  →  http://{host_ip}:55000
      API Docs    →  http://{host_ip}:55000/docs

    {Color.BOLD}Default login:{Color.RESET}
      Username:  admin
      Password:  admin
    """)
    )

    if not started:
        print(
            textwrap.dedent(f"""\
    {Color.BOLD}To start:{Color.RESET}
      cd {abs_path}
      docker compose up -d
    """)
        )

    print(
        textwrap.dedent(f"""\
    {Color.BOLD}Management:{Color.RESET}
      cd {abs_path}
      docker compose ps                # Service status
      docker compose logs -f           # View logs
      docker compose down              # Stop services
      docker compose pull && docker compose up -d   # Update to latest

    {Color.YELLOW}  ** Change the default admin password after first login! **{Color.RESET}
    """)
    )


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CyberSentinel DLP Server Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python3 install_dlp_server.py                         # Install & start
              python3 install_dlp_server.py /opt/cybersentinel      # Custom path
              python3 install_dlp_server.py --no-start              # Download & configure only
              python3 install_dlp_server.py --branch dev            # Different branch
        """),
    )
    parser.add_argument(
        "install_dir",
        nargs="?",
        default=DEFAULT_INSTALL_DIR,
        help=f"Installation directory (default: ./{DEFAULT_INSTALL_DIR})",
    )
    parser.add_argument(
        "--branch", "-b",
        default=DEFAULT_BRANCH,
        help=f"Git branch to fetch files from (default: {DEFAULT_BRANCH})",
    )
    parser.add_argument(
        "--no-start",
        action="store_true",
        help="Download and configure only — do not start services",
    )

    args = parser.parse_args()

    banner()

    # Step 1 — Prerequisites
    compose_cmd = check_prerequisites()

    # Step 2 — Download files
    download_all(args.install_dir, args.branch)

    # Step 3 — Generate .env
    generate_env(args.install_dir)

    host_ip = detect_host_ip()

    # Step 4 — Start services
    started = False
    if not args.no_start:
        docker_up(args.install_dir, compose_cmd)
        started = True

    # Summary
    print_summary(args.install_dir, host_ip, started)


if __name__ == "__main__":
    main()
