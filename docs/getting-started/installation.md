# Installation Guide

Complete setup instructions for BuildCPG Labs.

## System Requirements

- **Python:** 3.11 or higher
- **OS:** Mac 11+ or Linux (Windows with WSL2)
- **Memory:** 2GB minimum
- **Disk:** 1GB for base installation + data

## Step 1: Install Prerequisites

### Install Homebrew (Mac Only)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Install Python 3.11+

**Using Homebrew (Mac):**
```bash
brew install python@3.11
```

**Using System Package Manager (Linux):**
```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv
```

### Verify Installation
```bash
python3 --version
# Should show: Python 3.11.x or higher

pip --version
# Should show: pip 24.0 or higher
```

## Step 2: Clone Repository

### Using HTTPS
```bash
git clone https://github.com/narensham/buildcpg-labs.git
cd buildcpg-labs
```

### Or Using SSH
```bash
git clone git@github.com:narensham/buildcpg-labs.git
cd buildcpg-labs
```

## Step 3: Install Global Dependencies

These packages are needed at the root level:

```bash
pip install --upgrade pip
pip install pyyaml duckdb pandas mkdocs mkdocs-material
```

## Step 4: Verify Setup

### Check Python
```bash
python --version
# Should show: Python 3.11.x or higher
```

### Check Git
```bash
git --version
# Should show: git version 2.x or higher
```

### Check Directory Structure
```bash
ls -la
# Should show: shared/, config/, lab1_sales_performance/, mkdocs.yml, etc.
```

### Test Config
```bash
python config/paths.py
# Expected output:
# ✅ Lab1 config loaded: ...
# ✅ Lab1 DB path: /path/to/lab1_sales_performance/data/lab1_sales_performance.duckdb
```

## Step 5: Set Up Lab 1

### Create Lab Environment
```bash
cd lab1_sales_performance
python3 -m venv venv
source venv/bin/activate

# If using Mac Zsh and venv doesn't activate:
source venv/bin/activate
```

### Install Lab Dependencies
```bash
pip install -r requirements.txt
```

### Verify dbt
```bash
dbt --version
# Should show: dbt version 1.x.x
```

### Check dbt Configuration
```bash
cd dbt
dbt debug
# Should show: ✅ All checks passed!
```

## Step 6: Verify Everything Works

### Test Data Inspector
```bash
cd /path/to/buildcpg-labs/lab1_sales_performance
python scripts/inspect_data.py
# Should show: Schemas, tables, row counts
```

### Test CSV Monitor
```bash
python scripts/check_for_new_data.py
# Should show: CSV file info and last modification
```

### Test Config Access
```bash
cd /path/to/buildcpg-labs
python config/paths.py
# Should show: ✅ Config loaded successfully
```

## Alternative: Automated Setup Script

If you want to automate steps 1-5, create this script:

**File: `setup.sh`**
```bash
#!/bin/bash
set -e

echo "Setting up BuildCPG Labs..."

# Install global dependencies
echo "Installing global dependencies..."
pip install --upgrade pip
pip install pyyaml duckdb pandas mkdocs mkdocs-material

# Setup lab1
echo "Setting up lab1_sales_performance..."
cd lab1_sales_performance
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify
echo "Verifying setup..."
cd dbt
dbt debug

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  cd ../.. (go to root)"
echo "  cd lab1_sales_performance"
echo "  python scripts/inspect_data.py"
```

Run it:
```bash
chmod +x setup.sh
./setup.sh
```

## Troubleshooting Installation

### Python version error
```bash
# If python3 not found
which python3
python3 --version

# Try python (might be Python 2)
python --version
```

### pip command not found
```bash
# Use python -m pip instead
python -m pip install pyyaml
```

### venv activation fails on Mac
```bash
# Try direct path
source ./venv/bin/activate

# Or use Python's venv module directly
python -m venv venv
source venv/bin/activate
```

### dbt debug fails
```bash
# Make sure you're in the dbt directory
cd lab1_sales_performance/dbt
dbt debug

# If still fails, check dbt installation
pip show dbt-core dbt-duckdb
```

### Permission denied on setup.sh
```bash
chmod +x setup.sh
./setup.sh
```

## Post-Installation

After successful installation:

1. Read [Quick Start](quick-start.md)
2. Read [Architecture Overview](../architecture/overview.md)
3. Try your