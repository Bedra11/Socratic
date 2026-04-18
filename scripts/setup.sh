#!/bin/bash
# scripts/setup.sh
# Usage: bash scripts/setup.sh

echo "================================================"
echo "SOCRATIC PROJECT - FULL SETUP"
echo "================================================"

# stop if any command fails
set -e

# STEP 1 - Load .env
echo ""
echo "Loading environment variables..."

if [ -f ".env" ]; then
    export $(cat .env | grep -v '#' | grep '=' | xargs)
    echo "   .env loaded"
else
    echo "   .env not found - STOP"
    exit 1
fi

# STEP 2 - Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo "   Dependencies installed"

# STEP 3 - Create folders
echo ""
echo "Creating project folders..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p models
mkdir -p metrics
echo "   Folders ready"

# STEP 4 - Pull data from DVC
echo ""
echo "Pulling data from DVC remote..."
dvc pull
echo "   Data pulled from S3"

# STEP 5 - Verify files
echo ""
echo "Verifying files..."

MISSING=0
FILES=(
    "data/raw/ethics_dataset.csv"
    "data/raw/fallacy_dataset.csv"
    "data/raw/mappings.csv"
)

for f in "${FILES[@]}"; do
    if [ -f "$f" ]; then
        echo "   OK: $f"
    else
        echo "   MISSING: $f"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "Some files are missing - STOP"
    exit 1
fi

# DONE
echo ""
echo "================================================"
echo "SETUP COMPLETE - READY TO RUN PIPELINE"
echo "================================================"
echo ""
echo "Next step: dvc repro"