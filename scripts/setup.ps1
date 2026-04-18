# scripts/setup.ps1
# Usage: .\scripts\setup.ps1

Write-Host "================================================"
Write-Host "SOCRATIC PROJECT - FULL SETUP"
Write-Host "================================================"

# STEP 1 - Load .env
Write-Host "`nLoading environment variables..."

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [System.Environment]::SetEnvironmentVariable(
                $matches[1].Trim(),
                $matches[2].Trim(),
                "Process"
            )
        }
    }
    Write-Host "   .env loaded"
} else {
    Write-Host "   .env not found - STOP"
    exit 1
}

# STEP 2 - Install dependencies
Write-Host "`nInstalling dependencies..."
pip install -r requirements.txt --quiet
Write-Host "   Dependencies installed"

# STEP 3 - Create folders
Write-Host "`nCreating project folders..."
New-Item -ItemType Directory -Force -Path "data\raw"       | Out-Null
New-Item -ItemType Directory -Force -Path "data\processed"  | Out-Null
New-Item -ItemType Directory -Force -Path "models"          | Out-Null
New-Item -ItemType Directory -Force -Path "metrics"         | Out-Null
Write-Host "   Folders ready"

# STEP 4 - Pull data from DVC
Write-Host "`nPulling data from DVC remote..."
dvc pull
Write-Host "   Data pulled from S3"

# STEP 5 - Verify files
Write-Host "`nVerifying files..."

$files = @(
    "data\raw\ethics_dataset.csv",
    "data\raw\fallacy_dataset.csv",
    "data\raw\mappings.csv"
)

$missing = $false

foreach ($f in $files) {
    if (Test-Path $f) {
        Write-Host "   OK: $f"
    } else {
        Write-Host "   MISSING: $f"
        $missing = $true
    }
}

if ($missing) {
    Write-Host "`nSome files are missing - STOP"
    exit 1
}

# DONE
Write-Host "`n================================================"
Write-Host "SETUP COMPLETE - READY TO RUN PIPELINE"
Write-Host "================================================"
Write-Host "`nNext step: dvc repro"