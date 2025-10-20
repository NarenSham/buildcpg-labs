# Troubleshooting Guide

Solutions to common issues in BuildCPG Labs.

## Installation Issues

### Python Version Error
**Problem:** `python` command not found or shows Python 2.x

**Solution:**
```bash
# Check available versions
which python3
python3 --version

# Use python3 instead of python
python3 -m venv venv
python3 -m pip install pyyaml
```

### Virtual Environment Not Activating
**Problem:** `source venv/bin/activate` doesn't work on Mac

**Solution:**
```bash
# Try full path
source ./venv/bin/activate

# Or use this directly
./venv/bin/python --version

# For Zsh on newer Mac:
source venv/bin/activate
```

### pip: command not found
**Problem:** `pip install` doesn't work

**Solution:**
```bash
# Use python -m pip instead
python -m pip install pyyaml duckdb pandas

# Or upgrade pip
python -m pip install --upgrade pip
```

### Permission Denied Error
**Problem:** `permission denied: ./setup.sh`

**Solution:**
```bash
chmod +x setup.sh
./setup.sh
```

## dbt Issues

### dbt: command not found
**Problem:** `dbt run` or `dbt debug` doesn't work

**Solution:**
```bash
# Make sure you're in lab directory
cd lab1_sales_performance

# Make sure venv is activated
source venv/bin/activate

# Try again
dbt --version

# If still fails, reinstall
pip install dbt-duckdb
```

### dbt debug shows errors
**Problem:** `dbt debug` fails with configuration errors

**Solution:**
```bash
# Check you're in dbt directory
cd lab1_sales_performance/dbt

# Verify profiles.yml exists
ls -la profiles.yml

# Check dbt_project.yml
ls -la dbt_project.yml

# Run debug again
dbt debug
```

### Profile not found
**Problem:** `Profile 'lab1_duckdb' not found`

**Solution:**
```bash
# Check profiles.yml path
cat ~/.dbt/profiles.yml

# Or ensure it's in the lab directory
cd lab1_sales_performance/dbt
cat profiles.yml

# Update dbt_project.yml to point to correct profile
```

## Data Inspector Issues

### ModuleNotFoundError: No module named 'shared'
**Problem:** Python can't find shared utilities

**Solution:**
```bash
# Make sure you're in lab directory
cd lab1_sales_performance

# Run from correct location
python scripts/inspect_data.py

# Verify path in script
head -20 scripts/inspect_data.py
# Should show: sys.path.insert(0, '../..')
```

### FileNotFoundError: labs_config.yaml
**Problem:** Configuration file not found

**Solution:**
```bash
# Check file exists
ls -la config/labs_config.yaml

# Create if missing
touch config/labs_config.yaml

# Add content
cat > config/labs_config.yaml << 'EOF'
labs:
  lab1_sales_performance:
    path: lab1_sales_performance
    db_path: lab1_sales_performance/data/lab1_sales_performance.duckdb
    dbt_path: lab1_sales_performance/dbt
EOF
```

### Database file not found
**Problem:** `Cannot open file ".../lab1_sales_performance.duckdb"`

**Solution:**
```bash
# Check database exists
ls -la lab1_sales_performance/data/

# Create database by running dbt
cd lab1_sales_performance/dbt
dbt run

# Then try inspection again
cd ..
python scripts/inspect_data.py
```

## Git Issues

### Too many loose objects in repository
**Problem:** `warning: There are too many unreachable loose objects`

**Solution:**
```bash
# Remove gc.log if it exists
rm .git/gc.log 2>/dev/null || true

# Prune repository
git prune

# Optimize repository
git gc --aggressive
```

### venv directory accidentally committed
**Problem:** Tried to push and got huge file size

**Solution:**
```bash
# Remove from git tracking (keeps files on disk)
git rm -r --cached venv/
git rm -r --cached .venv/
git rm -r --cached dbt/target/

# Update .gitignore
echo "venv/" >> .gitignore
echo ".venv/" >> .gitignore
echo "dbt/target/" >> .gitignore

# Commit cleanup
git add .gitignore
git commit -m "Remove build artifacts from git"
```

## Makefile Issues

### make: command not found
**Problem:** `make` is not installed

**Solution (Mac):**
```bash
# Install Xcode command line tools
xcode-select --install

# Or install make directly
brew install make
```

**Solution (Linux):**
```bash
sudo apt-get update
sudo apt-get install make build-essential
```

### Tab indentation error in Makefile
**Problem:** `missing separator. Stop.` when running make

**Solution:**
```bash
# Makefiles require TAB indentation, not spaces
# Edit Makefile and ensure all recipe lines start with TAB

# In vim:
# :set noexpandtab

# In nano:
# Ctrl+I to insert tab

# Visual check:
cat -A Makefile | head -20
# Tabs show as ^I, spaces show as regular spaces
```

### venv not found when running make
**Problem:** `venv/bin/python: No such file or directory`

**Solution:**
```bash
# Run setup first
make setup

# This creates venv and installs dependencies
```

## Common Data Issues

### No schemas in database
**Problem:** `inspect_data.py` shows only 'main' and 'information_schema'

**Solution:**
```bash
# Tables haven't been created yet
# Create them with dbt
cd lab1_sales_performance/dbt
dbt run

# Then inspect again
cd ..
python scripts/inspect_data.py
```

### Quality score shows 0%
**Problem:** `get_quality_score` returns 0 even with good data

**Solution:**
```bash
# Check table has rows
python -c "
import sys
sys.path.insert(0, '../..')
from shared.utils.data_inspector import DataInspector
inspector = DataInspector('data/lab1_sales_performance.duckdb')
print(inspector.get_table_stats('raw', 'sales_data'))
"

# If rows = 0, data wasn't loaded
# Load it with dbt:
cd dbt
dbt run
```

### CSV says "no new data" but file was updated
**Problem:** `check_for_new_data.py` doesn't detect changes

**Solution:**
```bash
# State file might be outdated
# Remove it to reset detection
rm lab1_sales_performance/.csv_state.json

# Run again
cd lab1_sales_performance
python scripts/check_for_new_data.py
```

## Getting Help

### Enable Debug Logging
```bash
# For dbt:
dbt run --debug

# For Python scripts:
# Add this to beginning of script:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check File Permissions
```bash
# Verify script is executable
ls -la scripts/inspect_data.py

# Make executable if needed
chmod +x scripts/inspect_data.py
```

### Verify Directory Structure
```bash
# From buildcpg-labs root:
tree -L 2 -I '__pycache__|*.pyc|venv'

# Or list key files:
find . -name "dbt_project.yml" -o -name "labs_config.yaml" -o -name "Makefile"
```

### Check Disk Space
```bash
# Verify you have space
df -h

# Check database size
du -sh lab1_sales_performance/data/
```

## Still Stuck?

1. Check [FAQ](faq.md) for common questions
2. Review [Quick Start](getting-started/quick-start.md)
3. Check [Architecture](architecture/overview.md) to understand the design
4. Review the exact error message and search in this guide
5. Check git commit history for clues: `git log --oneline`  