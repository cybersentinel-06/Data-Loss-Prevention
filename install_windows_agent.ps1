<#
.SYNOPSIS
    CyberSentinel DLP - Windows Agent Installer (Non-Interactive)

.DESCRIPTION
    Downloads the agent executable and CA certificate from GitHub, creates
    configuration, installs the CA certificate, and sets up a scheduled task
    for auto-start — all in one command.

.PARAMETER ServerUrl
    Manager API URL (e.g., http://192.168.1.100:55000/api/v1)

.PARAMETER InstallDir
    Installation directory (default: C:\Program Files\CyberSentinel)

.PARAMETER NoStart
    Install and configure only — do not start the agent

.PARAMETER Force
    Overwrite existing installation

.EXAMPLE
    .\install_windows_agent.ps1 -ServerUrl "http://192.168.1.100:55000/api/v1"

.EXAMPLE
    # One-liner (download and run):
    irm https://raw.githubusercontent.com/cybersentinel-06/Data-Loss-Prevention/main/install_windows_agent.ps1 -OutFile $env:TEMP\install.ps1; & $env:TEMP\install.ps1 -ServerUrl "http://<SERVER-IP>:55000/api/v1"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerUrl,

    [string]$InstallDir = "C:\Program Files\CyberSentinel",

    [switch]$NoStart,

    [switch]$Force
)

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

$REPO_OWNER = "cybersentinel-06"
$REPO_NAME  = "Data-Loss-Prevention"
$BRANCH     = "main"
$RAW_BASE   = "https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/$BRANCH"

$EXE_NAME    = "cybersentinel_agent.exe"
$CONFIG_NAME = "agent_config.json"
$CERT_NAME   = "ca.cer"
$TASK_NAME   = "CyberSentinelDLPAgent"

# Files to download: remote path -> local filename
$AGENT_FILES = @(
    @{ Remote = "agents/endpoint/windows/cybersentinel_agent.exe"; Local = $EXE_NAME },
    @{ Remote = "agents/endpoint/windows/ca.cer"; Local = $CERT_NAME }
)

# ─────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║   CyberSentinel DLP - Windows Agent Installer    ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Info    { param([string]$Msg) Write-Host "  [INFO]  $Msg" -ForegroundColor Cyan }
function Write-Ok      { param([string]$Msg) Write-Host "  [ OK ]  $Msg" -ForegroundColor Green }
function Write-Warn    { param([string]$Msg) Write-Host "  [WARN]  $Msg" -ForegroundColor Yellow }
function Write-Err     { param([string]$Msg) Write-Host "  [FAIL]  $Msg" -ForegroundColor Red }

function Test-Administrator {
    $identity  = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ─────────────────────────────────────────────
# Step 1: Prerequisites
# ─────────────────────────────────────────────

function Step-Prerequisites {
    Write-Host "`n  [1/5] Checking prerequisites`n" -ForegroundColor White

    # Admin check
    if (-not (Test-Administrator)) {
        Write-Err "This installer must be run as Administrator"
        Write-Err "Right-click PowerShell and select 'Run as Administrator'"
        exit 1
    }
    Write-Ok "Running as Administrator"

    # Windows version
    $os = [System.Environment]::OSVersion
    Write-Ok "Windows $($os.Version) ($($os.Platform))"

    # Network check
    try {
        $null = [System.Net.Dns]::GetHostEntry("github.com")
        Write-Ok "Network connectivity OK"
    } catch {
        Write-Err "Cannot resolve github.com — check network connectivity"
        exit 1
    }
}

# ─────────────────────────────────────────────
# Step 2: Download agent files
# ─────────────────────────────────────────────

function Step-DownloadFiles {
    Write-Host "`n  [2/5] Downloading agent files`n" -ForegroundColor White

    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
        Write-Ok "Created directory: $InstallDir"
    }

    foreach ($file in $AGENT_FILES) {
        $url  = "$RAW_BASE/$($file.Remote)"
        $dest = Join-Path $InstallDir $file.Local

        if ((Test-Path $dest) -and -not $Force) {
            Write-Warn "$($file.Local) already exists (use -Force to overwrite)"
            continue
        }

        Write-Info "Downloading $($file.Local)..."
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -ErrorAction Stop
            Write-Ok "$($file.Local) downloaded"
        } catch {
            Write-Err "Failed to download $($file.Local): $_"
            exit 1
        }
    }

    Write-Ok "Agent files saved to $InstallDir"
}

# ─────────────────────────────────────────────
# Step 3: Install CA Certificate
# ─────────────────────────────────────────────

function Step-InstallCertificate {
    Write-Host "`n  [3/5] Installing CA certificate`n" -ForegroundColor White

    $certPath = Join-Path $InstallDir $CERT_NAME

    if (-not (Test-Path $certPath)) {
        Write-Warn "CA certificate not found at $certPath — skipping"
        return
    }

    try {
        $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certPath)
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store(
            [System.Security.Cryptography.X509Certificates.StoreName]::Root,
            [System.Security.Cryptography.X509Certificates.StoreLocation]::LocalMachine
        )
        $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
        $store.Add($cert)
        $store.Close()
        Write-Ok "CA certificate installed to Trusted Root store"
    } catch {
        Write-Warn "Failed to install CA certificate: $_"
        Write-Warn "HTTPS connections to the server may fail"
    }
}

# ─────────────────────────────────────────────
# Step 4: Generate configuration
# ─────────────────────────────────────────────

function Step-GenerateConfig {
    Write-Host "`n  [4/5] Generating agent configuration`n" -ForegroundColor White

    $configPath = Join-Path $InstallDir $CONFIG_NAME

    # Normalize server URL — strip trailing slash
    $normalizedUrl = $ServerUrl.TrimEnd("/")

    if ((Test-Path $configPath) -and -not $Force) {
        Write-Info "Existing config found — updating server_url only"
        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json
            $config.server_url = $normalizedUrl
            $config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
            Write-Ok "Config updated: $configPath"
            Write-Ok "Agent ID: $($config.agent_id)"
            return
        } catch {
            Write-Warn "Could not update existing config: $_ — creating new one"
        }
    }

    $hostname = $env:COMPUTERNAME
    $agentId  = [guid]::NewGuid().ToString()

    $config = @{
        server_url           = $normalizedUrl
        agent_id             = $agentId
        agent_name           = $hostname
        heartbeat_interval   = 30
        policy_sync_interval = 60
    }

    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8

    Write-Ok "Config written: $configPath"
    Write-Ok "Agent ID:       $agentId"
    Write-Ok "Agent name:     $hostname"
    Write-Ok "Server URL:     $normalizedUrl"
}

# ─────────────────────────────────────────────
# Step 5: Create Scheduled Task (auto-start)
# ─────────────────────────────────────────────

function Step-CreateScheduledTask {
    Write-Host "`n  [5/5] Setting up scheduled task`n" -ForegroundColor White

    $exePath = Join-Path $InstallDir $EXE_NAME

    # Remove existing task if present
    $existing = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
    if ($existing) {
        if ($Force) {
            Unregister-ScheduledTask -TaskName $TASK_NAME -Confirm:$false
            Write-Info "Removed existing scheduled task"
        } else {
            Write-Warn "Scheduled task '$TASK_NAME' already exists (use -Force to recreate)"
            if (-not $NoStart) {
                Write-Info "Starting agent..."
                Start-ScheduledTask -TaskName $TASK_NAME
                Write-Ok "Agent started"
            }
            return
        }
    }

    # Create scheduled task that runs at system startup with SYSTEM privileges
    $action  = New-ScheduledTaskAction -Execute $exePath -WorkingDirectory $InstallDir
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit (New-TimeSpan -Days 365)

    Register-ScheduledTask `
        -TaskName $TASK_NAME `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "CyberSentinel DLP Endpoint Agent" | Out-Null

    Write-Ok "Scheduled task '$TASK_NAME' created (runs at startup as SYSTEM)"

    if (-not $NoStart) {
        Write-Info "Starting agent..."
        Start-ScheduledTask -TaskName $TASK_NAME
        Start-Sleep -Seconds 2

        # Check if process is running
        $proc = Get-Process -Name "cybersentinel_agent" -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Ok "Agent is running (PID: $($proc.Id))"
        } else {
            Write-Warn "Agent may not have started — check logs in $InstallDir"
        }
    } else {
        Write-Info "Task created but agent not started (-NoStart)"
    }
}

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────

function Write-Summary {
    $normalizedUrl = $ServerUrl.TrimEnd("/")
    $started = -not $NoStart

    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║          Installation Complete                    ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Server URL:    $normalizedUrl" -ForegroundColor White
    Write-Host "  Install path:  $InstallDir" -ForegroundColor White
    Write-Host "  Config:        $(Join-Path $InstallDir $CONFIG_NAME)" -ForegroundColor White
    Write-Host "  Task name:     $TASK_NAME" -ForegroundColor White
    Write-Host "  Status:        $(if ($started) { 'Running' } else { 'Not started' })" -ForegroundColor White
    Write-Host ""
    Write-Host "  Useful Commands:" -ForegroundColor White
    Write-Host "    Get-ScheduledTask -TaskName $TASK_NAME        # Check task status"
    Write-Host "    Start-ScheduledTask -TaskName $TASK_NAME      # Start agent"
    Write-Host "    Stop-ScheduledTask -TaskName $TASK_NAME       # Stop agent"
    Write-Host "    Get-Process cybersentinel_agent                # Check if running"
    Write-Host ""
    Write-Host "  Uninstall:" -ForegroundColor White
    Write-Host "    Stop-ScheduledTask -TaskName $TASK_NAME"
    Write-Host "    Unregister-ScheduledTask -TaskName $TASK_NAME -Confirm:`$false"
    Write-Host "    Remove-Item -Recurse -Force '$InstallDir'"
    Write-Host ""
}

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

Write-Banner

Step-Prerequisites
Step-DownloadFiles
Step-InstallCertificate
Step-GenerateConfig
Step-CreateScheduledTask

Write-Summary
