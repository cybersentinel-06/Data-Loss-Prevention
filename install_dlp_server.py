#!/usr/bin/env python3
"""
CyberSentinel DLP Server - Remote Installer

Downloads and sets up the DLP server stack (API + Dashboard + Databases)
from the GitHub repository. Only fetches server-relevant files.

Usage:
    python3 install_dlp_server.py                  # Install to ./cybersentinel-dlp
    python3 install_dlp_server.py /opt/dlp         # Install to custom path
    python3 install_dlp_server.py --branch dev     # Install from a specific branch
"""

import argparse
import hashlib
import io
import json
import os
import platform
import secrets
import shutil
import socket
import subprocess
import sys
import tarfile
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

# Directories/files to extract from the repo tarball.
# Everything else (agents/, scripts/, .github/, docs) is skipped.
INCLUDE_PATHS = [
    "server/",
    "dashboard/",
    "database/",
    "config/",
    "docker-compose.yml",
    "docker-compose.prod.yml",
    ".env.example",
    "deploy.sh",
    "deploy-ubuntu.sh",
    "Makefile",
    "README.md",
    "INSTALLATION_GUIDE.md",
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

def check_command(cmd, friendly_name):
    """Return True if *cmd* is on PATH."""
    return shutil.which(cmd) is not None


def check_prerequisites():
    """Verify Docker and Docker Compose are available."""
    print(f"\n{Color.BOLD}[1/5] Checking prerequisites{Color.RESET}\n")
    all_ok = True

    # Python version
    if sys.version_info >= (3, 8):
        ok(f"Python {platform.python_version()}")
    else:
        err(f"Python >= 3.8 required (found {platform.python_version()})")
        all_ok = False

    # Docker
    if check_command("docker", "Docker"):
        try:
            ver = subprocess.check_output(
                ["docker", "--version"], stderr=subprocess.DEVNULL, text=True
            ).strip()
            ok(f"Docker found  ({ver})")
        except subprocess.CalledProcessError:
            ok("Docker found")
    else:
        err("Docker not found. Install: https://docs.docker.com/engine/install/")
        all_ok = False

    # Docker Compose (v2 plugin or standalone)
    compose_cmd = None
    for candidate in (["docker", "compose", "version"], ["docker-compose", "--version"]):
        try:
            subprocess.check_output(candidate, stderr=subprocess.DEVNULL, text=True)
            compose_cmd = candidate[:-1]  # drop the version arg
            ok(f"Docker Compose found  ({' '.join(candidate[:-1])})")
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    if compose_cmd is None:
        err("Docker Compose not found. Install: https://docs.docker.com/compose/install/")
        all_ok = False

    if not all_ok:
        err("Please install missing prerequisites and re-run the installer.")
        sys.exit(1)

    return compose_cmd


# ──────────────────────────────────────────────
# Download & extract
# ──────────────────────────────────────────────

def download_tarball(branch):
    """Download the repo tarball from GitHub and return the bytes."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/tarball/{branch}"
    info(f"Downloading from {REPO_OWNER}/{REPO_NAME} (branch: {branch}) ...")

    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            err(f"Repository or branch not found: {REPO_OWNER}/{REPO_NAME}@{branch}")
        else:
            err(f"GitHub API error: {exc.code} {exc.reason}")
        sys.exit(1)
    except urllib.error.URLError as exc:
        err(f"Network error: {exc.reason}")
        sys.exit(1)

    size_mb = len(data) / (1024 * 1024)
    ok(f"Downloaded {size_mb:.1f} MB")
    return data


def should_extract(member_name, prefix):
    """
    Decide if a tarball member should be extracted.
    *member_name* has the GitHub prefix (e.g. owner-repo-sha/server/...).
    """
    # Strip the top-level GitHub directory prefix
    rel = member_name[len(prefix):] if member_name.startswith(prefix) else member_name

    for inc in INCLUDE_PATHS:
        if inc.endswith("/"):
            # Directory prefix match
            if rel.startswith(inc) or rel == inc.rstrip("/"):
                return True
        else:
            # Exact file match
            if rel == inc:
                return True
    return False


def extract_server_files(tarball_bytes, install_dir):
    """Extract only server-relevant files into *install_dir*."""
    print(f"\n{Color.BOLD}[2/5] Extracting server files{Color.RESET}\n")

    os.makedirs(install_dir, exist_ok=True)

    buf = io.BytesIO(tarball_bytes)
    extracted = 0

    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        # Discover the top-level prefix GitHub adds (e.g. "owner-repo-commitsha/")
        members = tar.getmembers()
        if not members:
            err("Tarball is empty.")
            sys.exit(1)

        prefix = members[0].name.split("/")[0] + "/"

        for member in members:
            if not should_extract(member.name, prefix):
                continue

            # Rewrite the member path: strip GitHub prefix, prepend install_dir
            rel_path = member.name[len(prefix):]
            if not rel_path:
                continue

            member_copy = tarfile.TarInfo(name=rel_path)
            member_copy.size = member.size
            member_copy.mode = member.mode
            member_copy.type = member.type

            dest = os.path.join(install_dir, rel_path)

            if member.isdir():
                os.makedirs(dest, exist_ok=True)
            elif member.isfile():
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with tar.extractfile(member) as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                # Preserve executable bit
                os.chmod(dest, member.mode)
                extracted += 1

    ok(f"Extracted {extracted} files into {os.path.abspath(install_dir)}/")
    return extracted


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
    print(f"\n{Color.BOLD}[3/5] Generating environment configuration{Color.RESET}\n")

    example = os.path.join(install_dir, ".env.example")
    env_file = os.path.join(install_dir, ".env")

    if os.path.exists(env_file):
        warn(".env already exists — skipping generation (keeping existing config)")
        return

    if not os.path.exists(example):
        warn(".env.example not found — skipping env generation")
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
        "SERVER-IP": host_ip,
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
# Post-extraction setup
# ──────────────────────────────────────────────

def make_scripts_executable(install_dir):
    """Ensure shell scripts have the executable bit set."""
    for name in ("deploy.sh", "deploy-ubuntu.sh"):
        path = os.path.join(install_dir, name)
        if os.path.exists(path):
            os.chmod(path, 0o755)


def create_runtime_dirs(install_dir):
    """Create directories that docker-compose volume mounts expect."""
    for d in ("quarantine", "config"):
        path = os.path.join(install_dir, d)
        os.makedirs(path, exist_ok=True)


# ──────────────────────────────────────────────
# Build & launch (optional)
# ──────────────────────────────────────────────

def docker_build(install_dir, compose_cmd):
    """Run docker compose build."""
    print(f"\n{Color.BOLD}[4/5] Building Docker images{Color.RESET}\n")
    info("This may take several minutes on first run ...")

    cmd = compose_cmd + ["build"]
    result = subprocess.run(cmd, cwd=install_dir)
    if result.returncode != 0:
        err("Docker build failed. Check the output above for details.")
        sys.exit(1)
    ok("Docker images built successfully")


def docker_up(install_dir, compose_cmd):
    """Run docker compose up -d."""
    print(f"\n{Color.BOLD}[5/5] Starting services{Color.RESET}\n")

    cmd = compose_cmd + ["up", "-d"]
    result = subprocess.run(cmd, cwd=install_dir)
    if result.returncode != 0:
        err("Failed to start services. Check the output above for details.")
        sys.exit(1)
    ok("All services started")


# ──────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────

def print_summary(install_dir, host_ip, built, started):
    abs_path = os.path.abspath(install_dir)
    status_build = f"{Color.GREEN}Done{Color.RESET}" if built else f"{Color.YELLOW}Skipped{Color.RESET}"
    status_start = f"{Color.GREEN}Running{Color.RESET}" if started else f"{Color.YELLOW}Skipped{Color.RESET}"

    print(
        textwrap.dedent(f"""
    {Color.CYAN}{Color.BOLD}
    ╔══════════════════════════════════════════════════╗
    ║          Installation Complete                   ║
    ╚══════════════════════════════════════════════════╝{Color.RESET}

    {Color.BOLD}Install path:{Color.RESET}  {abs_path}
    {Color.BOLD}Docker build:{Color.RESET}  {status_build}
    {Color.BOLD}Services:    {Color.RESET}  {status_start}

    {Color.BOLD}Endpoints:{Color.RESET}
      Dashboard   →  http://{host_ip}:3000
      API Server  →  http://{host_ip}:55000
      API Docs    →  http://{host_ip}:55000/docs

    {Color.BOLD}Default login:{Color.RESET}
      Email:     admin@cybersentinel.local
      Password:  ChangeMe123!

    {Color.BOLD}Next steps:{Color.RESET}
      cd {abs_path}
    """)
    )

    if not built:
        print(f"      docker compose build        # Build images")
    if not started:
        print(f"      docker compose up -d         # Start services")

    print(
        textwrap.dedent(f"""
      ./deploy.sh status              # Check service health
      ./deploy.sh logs                # View logs
      ./deploy.sh stop                # Stop services

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
              python3 install_dlp_server.py                         # Default install
              python3 install_dlp_server.py /opt/cybersentinel      # Custom path
              python3 install_dlp_server.py --branch dev            # Different branch
              python3 install_dlp_server.py --build --start         # Build & start immediately
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
        help=f"Git branch to install from (default: {DEFAULT_BRANCH})",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build Docker images after downloading",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start services after building (implies --build)",
    )

    args = parser.parse_args()

    if args.start:
        args.build = True

    banner()

    # Step 1 — Prerequisites
    compose_cmd = check_prerequisites()

    # Step 2 — Download & extract
    tarball = download_tarball(args.branch)
    count = extract_server_files(tarball, args.install_dir)
    if count == 0:
        err("No files extracted. Check that the repository and branch exist.")
        sys.exit(1)

    # Post-extraction housekeeping
    make_scripts_executable(args.install_dir)
    create_runtime_dirs(args.install_dir)

    # Step 3 — Generate .env
    generate_env(args.install_dir)

    host_ip = detect_host_ip()

    # Step 4 — Build (optional)
    built = False
    if args.build:
        docker_build(args.install_dir, compose_cmd)
        built = True

    # Step 5 — Start (optional)
    started = False
    if args.start:
        docker_up(args.install_dir, compose_cmd)
        started = True

    # Summary
    print_summary(args.install_dir, host_ip, built, started)


if __name__ == "__main__":
    main()
