# BuildCPG Labs

A modern, scalable data engineering platform for managing multiple independent labs using dbt, DuckDB, and Python.

## Overview

BuildCPG Labs enables you to:

- **Run independent labs** - Each lab has its own database and data, shares Python environment
- **Share utilities** - Common code used by all labs without duplication
- **Scale easily** - Create new labs in minutes (with shared dependencies)
- **Maintain quality** - Built-in data inspection and quality checks
- **Work efficiently** - Single venv, manual profile switching for simplicity

## Key Features

### Multi-Lab Architecture with Shared Environment

Each lab is data-independent but shares the Python environment:

```
buildcpg-labs/
├── .venv/                      # SINGLE venv (shared by all labs)
├── shared/                     # Reusable utilities (used by ALL labs)
│   ├── utils/                  # DataInspector, CSVMonitor
│   └── config/                 # Central configuration (inside shared)
├── lab1_sales_performance/     # Lab 1 (independent data)
├── lab2_forecast_model/        # Lab 2 (independent data)
└── lab3_customer_segmentation/ # Lab 3 (independent data)
```

**Current Architecture:**
- ✅ **One venv** - All labs share Python environment (~500MB total)
- ✅ **Independent data** - Each lab has its own DuckDB database
- ⚠️ **Manual switching** - Edit `profiles.yml` when changing labs
- ⚠️ **Same dependencies** - All labs must use compatible packages

See [Current Setup](architecture/current-setup.md) for detailed analysis.

### Shared Utilities

Work with any lab's database using common tools:

```python
# Inspect lab1 database
from shared.utils.data_inspector import DataInspector
inspector = DataInspector('lab1_sales_performance/data/lab1.duckdb')
quality = inspector.get_quality_score('gold', 'summary')
```

### Workflow: Switching Between Labs

```bash
# Activate venv once
source .venv/bin/activate

# Work on lab1
cd lab1_sales_performance/dbt
dbt debug  # Verify profiles.yml points to lab1.duckdb
dbt run

# Switch to lab2
cd ../../lab2_forecast_model/dbt
# Edit profiles.yml to point to lab2.duckdb
dbt debug  # Verify correct database
dbt run
```

⚠️ **Always run `dbt debug` before `dbt run` to verify correct database connection.**

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/narensham/buildcpg-labs.git
cd buildcpg-labs
```

### 2. Setup Shared Environment
```bash
# Create single venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install pyyaml duckdb pandas dbt-duckdb
```

### 3. Work with Lab 1
```bash
cd lab1_sales_performance/dbt
dbt debug  # Verify connection
dbt run    # Run transformations

# Inspect results
cd ..
python scripts/inspect_data.py
```

### 4. Create Lab 2 (Future)
```bash
cd ../..
./setup_new_lab.sh lab2_forecast_model
cd lab2_forecast_model/dbt
# Edit profiles.yml with lab2 database path
dbt debug
dbt run
```

## Documentation Structure

- **[Getting Started](getting-started/quick-start.md)** - Setup and first steps
- **[Architecture](architecture/overview.md)** - Design and concepts
- **[Current Setup](architecture/current-setup.md)** - Single venv approach explained
- **[Phases](phases/phase1-foundation.md)** - Implementation phases
- **[Utilities](utilities/data-inspector.md)** - Shared tools reference
- **[Troubleshooting](troubleshooting.md)** - Common issues and fixes

## Project Status

### Phase 1: Foundation ✅
- Shared utilities (DataInspector, CSVMonitor)
- Central configuration (`shared/config/`)
- Lab1 inspection scripts
- Single venv setup

### Phase 2: Automation (Planned)
- Profile switching helpers
- Safety checks before dbt run
- Lab creation templates
- Documentation updates

### Phase 3+: Future
- Per-lab venvs (when needed)
- Orchestration (Airflow/Prefect)
- Advanced monitoring
- Data quality gates

## Current Setup: Pros & Cons

### Advantages ✅
- **Space efficient** - One venv (~500MB) vs per-lab venvs (~500MB × N)
- **Consistent packages** - All labs use same versions
- **Simple setup** - Install dependencies once
- **Quick switching** - Just edit profiles.yml

### Trade-offs ⚠️
- **No dependency isolation** - All labs must use compatible packages
- **Manual profile switching** - Edit profiles.yml when changing labs
- **Risk of errors** - Possible to run dbt on wrong database
- **No concurrent work** - Can't work on multiple labs simultaneously

**Recommendation:** Current setup works well for 1-2 labs with single developer. Consider migrating to per-lab venvs when you have 3+ labs or multiple team members.

See [Current Setup Analysis](architecture/current-setup.md) for full details.

## Requirements

- Python 3.11+
- Mac 11+ or Linux (no Docker required)
- Git
- Discipline for profile switching

## Common Tasks

### Check Which Database You're Connected To
```bash
cd lab1_sales_performance/dbt
dbt debug | grep path
# Should show: path: ../data/lab1_sales_performance.duckdb
```

### Inspect Data Quality
```bash
cd lab1_sales_performance
python scripts/inspect_data.py
# Shows: schemas, tables, row counts, quality scores
```

### Monitor New Data
```bash
python scripts/check_for_new_data.py
# Shows: if CSV was updated, new row count
```

## Safety Tips

### Before Running dbt

```bash
# 1. Check current directory
pwd

# 2. Verify profiles.yml
cat dbt/profiles.yml | grep path

# 3. Run debug to confirm
dbt debug

# 4. Then run pipeline
dbt run
```

### Prevent Wrong Database Writes

Create an alias in `~/.zshrc`:

```bash
alias dbt-safe='dbt debug && read -q "REPLY?Continue with dbt run? (y/n) " && dbt run'
```

Usage:
```bash
dbt-safe  # Shows database, asks for confirmation
```

## Support

- 📖 **[Read the docs](getting-started/quick-start.md)**
- ❓ **[Check FAQ](faq.md)**
- 🔧 **[Troubleshooting](troubleshooting.md)**
- ⚠️ **[Current Setup Details](architecture/current-setup.md)**

---

**Architecture:** Single shared venv + independent data per lab  
**Last Updated:** January 2025  
**Maintainer:** narensham  
**Repository:** [GitHub](https://github.com/narensham/buildcpg-labs)