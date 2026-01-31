# Mini Agent Configuration Setup Script for Windows
# This script helps you set up Mini Agent configuration files

# Error handling
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )

    $colorMap = @{
        "Red" = [ConsoleColor]::Red
        "Green" = [ConsoleColor]::Green
        "Yellow" = [ConsoleColor]::Yellow
        "Blue" = [ConsoleColor]::Blue
        "Cyan" = [ConsoleColor]::Cyan
        "White" = [ConsoleColor]::White
    }

    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

# Configuration directory
$CONFIG_DIR = Join-Path $env:USERPROFILE ".mini-agent\config"

Write-ColorOutput "==================================================" -Color "Cyan"
Write-ColorOutput "   Mini Agent Configuration Setup" -Color "Cyan"
Write-ColorOutput "==================================================" -Color "Cyan"
Write-Host ""

# Step 1: Create config directory
Write-ColorOutput "[1/2] Creating configuration directory..." -Color "Blue"

if (Test-Path $CONFIG_DIR) {
    # Auto backup existing config
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $BACKUP_DIR = Join-Path $env:USERPROFILE ".mini-agent\config.backup.$timestamp"
    Write-ColorOutput "   Configuration directory exists, backing up to:" -Color "Yellow"
    Write-ColorOutput "   $BACKUP_DIR" -Color "Yellow"
    Copy-Item -Path $CONFIG_DIR -Destination $BACKUP_DIR -Recurse
    Write-ColorOutput "   [OK] Backup created" -Color "Green"
} else {
    New-Item -Path $CONFIG_DIR -ItemType Directory -Force | Out-Null
    Write-ColorOutput "   [OK] Created: $CONFIG_DIR" -Color "Green"
}

# Step 2: Download configuration files from GitHub
Write-ColorOutput "[2/2] Downloading configuration files..." -Color "Blue"

$FILES_COPIED = 0
$GITHUB_RAW_URL = "https://raw.githubusercontent.com/MiniMax-AI/Mini-Agent/main/mini_agent/config"

# Download config-example.yaml as config.yaml
try {
    $configUrl = "$GITHUB_RAW_URL/config-example.yaml"
    $configPath = Join-Path $CONFIG_DIR "config.yaml"
    Invoke-WebRequest -Uri $configUrl -OutFile $configPath -UseBasicParsing
    Write-ColorOutput "   [OK] Downloaded: config.yaml" -Color "Green"
    $FILES_COPIED++
} catch {
    Write-ColorOutput "   [ERROR] Failed to download: config.yaml" -Color "Red"
}

# Download mcp-example.json as mcp.json
try {
    $mcpUrl = "$GITHUB_RAW_URL/mcp-example.json"
    $mcpPath = Join-Path $CONFIG_DIR "mcp.json"
    Invoke-WebRequest -Uri $mcpUrl -OutFile $mcpPath -UseBasicParsing
    Write-ColorOutput "   [OK] Downloaded: mcp.json" -Color "Green"
    $FILES_COPIED++
} catch {
    # Optional file
}

# Download system_prompt.md
try {
    $promptUrl = "$GITHUB_RAW_URL/system_prompt.md"
    $promptPath = Join-Path $CONFIG_DIR "system_prompt.md"
    Invoke-WebRequest -Uri $promptUrl -OutFile $promptPath -UseBasicParsing
    Write-ColorOutput "   [OK] Downloaded: system_prompt.md" -Color "Green"
    $FILES_COPIED++
} catch {
    # Optional file
}

if ($FILES_COPIED -eq 0) {
    Write-ColorOutput "   [ERROR] Failed to download configuration files" -Color "Red"
    Write-ColorOutput "   Please check your internet connection" -Color "Yellow"
    exit 1
}

Write-ColorOutput "   [OK] Configuration files ready" -Color "Green"

Write-Host ""
Write-ColorOutput "==================================================" -Color "Green"
Write-ColorOutput "   Setup Complete!" -Color "Green"
Write-ColorOutput "==================================================" -Color "Green"
Write-Host ""
Write-Host "Configuration files location:"
Write-ColorOutput "  $CONFIG_DIR" -Color "Cyan"
Write-Host ""
Write-Host "Files:"
Get-ChildItem $CONFIG_DIR -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "   $($_.Name)"
}
Write-Host ""
Write-ColorOutput "Next Steps:" -Color "Yellow"
Write-Host ""
Write-ColorOutput "1. Install Mini Agent:" -Color "Yellow"
Write-ColorOutput "   pipx install git+https://github.com/MiniMax-AI/Mini-Agent.git" -Color "Green"
Write-Host ""
Write-ColorOutput "2. Configure your API Key:" -Color "Yellow"
Write-Host "   Edit config.yaml and add your MiniMax API Key:"
Write-ColorOutput "   notepad $CONFIG_DIR\config.yaml" -Color "Green"
Write-ColorOutput "   code $CONFIG_DIR\config.yaml" -Color "Green"
Write-Host ""
Write-ColorOutput "3. Start using Mini Agent:" -Color "Yellow"
Write-ColorOutput "   mini-agent                              # Use current directory" -Color "Green"
Write-ColorOutput "   mini-agent --workspace C:\path\to\project # Specify workspace" -Color "Green"
Write-ColorOutput "   mini-agent --help                      # Show help" -Color "Green"
Write-Host ""
