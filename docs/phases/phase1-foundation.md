# Phase 1: Foundation

Establish shared utilities and central configuration that all labs use.

## What Phase 1 Delivers

✅ **Shared Utilities** - DataInspector, CSVMonitor, Config Loaders  
✅ **Central Configuration** - Lab registry, path management  
✅ **Lab1 Scripts** - Data inspection and monitoring  
✅ **Clean Git History** - No build artifacts or venv  

## What Gets Created

```
buildcpg-labs/
├── shared/                          ← NEW
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_inspector.py       # Database inspection
│   │   ├── csv_monitor.py          # Detect new data
│   │   └── config_loader.py        # Load configurations
│   │
│   ├── data_quality/
│   │   ├── validators.py           # Validation rules
│   │   └── expectations.py         # Data expectations
│   │
│   └── templates/                  ← For Phase 2
│       └── (templates will go here)
│
├── config/                          ← NEW
│   ├── labs_config.yaml            # Lab registry
│   └── paths.py                    # Path helpers
│
└── lab1_sales_performance/         ← UPDATED
    ├── scripts/
    │   ├── inspect_data.py         # NEW - uses shared utilities
    │   └── check_for_new_data.py   # NEW - uses shared utilities
    └── .gitignore                  # NEW - ignore venv, artifacts
```

## Step-by-Step Setup

### Step 1: Create Directory Structure
```bash
cd buildcpg-labs
mkdir -p shared/utils
mkdir -p shared/data_quality
mkdir -p shared/templates
mkdir -p config

# Create __init__.py files
touch shared/__init__.py
touch shared/utils/__init__.py
touch shared/data_quality/__init__.py
```

### Step 2: Create Shared Utilities
Create these files in `shared/utils/`:

- `data_inspector.py` - Inspect databases
- `csv_monitor.py` - Monitor CSV changes
- `config_loader.py` - Load lab configurations

See documentation links below.

### Step 3: Create Configuration
Create these files in `config/`:

- `labs_config.yaml` - Central lab registry
- `paths.py` - Path helpers for accessing labs

### Step 4: Create Lab1 Scripts
Create these files in `lab1_sales_performance/scripts/`:

- `inspect_data.py` - Inspect lab1 database using shared DataInspector
- `check_for_new_data.py` - Monitor lab1 CSV using shared CSVMonitor

### Step 5: Add Git Ignore
Create `.gitignore` at root and `lab1_sales_performance/.gitignore`

### Step 6: Test Everything Works
```bash
# Test shared utilities
python shared/utils/data_inspector.py
python shared/utils/csv_monitor.py

# Test config
python config/paths.py

# Test lab1 scripts
cd lab1_sales_performance
python scripts/inspect_data.py
python scripts/check_for_new_data.py
```

### Step 7: Commit to Git
```bash
git add shared/
git add config/
git add lab1_sales_performance/scripts/
git add .gitignore
git add lab1_sales_performance/.gitignore

git commit -m "Phase 1: Create shared utilities and foundational structure"
git push origin main
```

## How It Works

### Shared Utilities
Written once in `shared/`, used by all labs:

```python
# In lab1_sales_performance/scripts/inspect_data.py
import sys
sys.path.insert(0, '../..')  # Go to root
from shared.utils.data_inspector import DataInspector

inspector = DataInspector('data/lab1_sales_performance.duckdb')
quality = inspector.get_quality_score('gold', 'gold_orders_summary')
```

```python
# In lab2_forecast_model/scripts/inspect_data.py (FUTURE)
import sys
sys.path.insert(0, '../..')  # Go to root
from shared.utils.data_inspector import DataInspector

inspector = DataInspector('data/lab2_forecast_model.duckdb')
quality = inspector.get_quality_score('gold', 'forecast_summary')
# Same code, different database
```

### Central Configuration
All labs registered in one place:

```yaml
# config/labs_config.yaml
labs:
  lab1_sales_performance:
    path: lab1_sales_performance
    db_path: lab1_sales_performance/data/lab1_sales_performance.duckdb
    dbt_path: lab1_sales_performance/dbt
    
  lab2_forecast_model:  # When created
    path: lab2_forecast_model
    db_path: lab2_forecast_model/data/lab2_forecast_model.duckdb
    dbt_path: lab2_forecast_model/dbt
```

## Verification Checklist

After Phase 1 completion, verify:

- [ ] `shared/` directory exists with utilities
- [ ] `config/` directory exists with labs_config.yaml and paths.py
- [ ] `lab1_sales_performance/scripts/inspect_data.py` works
- [ ] `lab1_sales_performance/scripts/check_for_new_data.py` works
- [ ] `python config/paths.py` returns ✅
- [ ] `git status` shows clean working tree
- [ ] Changes committed to git

## What's NOT Included Yet

Phase 1 focuses on foundation. These come later:

- ❌ Makefile (Phase 2)
- ❌ Bootstrap script (Phase 2)
- ❌ Orchestration/Airflow (Phase 3)
- ❌ Advanced monitoring (Phase 3+)

## Troubleshooting Phase 1

### Import Error: "No module named 'shared'"
Make sure you're running scripts from the right directory:
```bash
cd lab1_sales_performance
python scripts/inspect_data.py  # Works
python -c "import scripts.inspect_data"  # Also works
```

### File Not Found: "labs_config.yaml"
Verify the path exists:
```bash
ls -la config/labs_config.yaml
```

### DataInspector returns empty schemas
Database might not have tables yet. Create some with dbt:
```bash
cd lab1_sales_performance/dbt
dbt run
```

See [Troubleshooting](../troubleshooting.md) for more help.

## Next Phase

Phase 2 adds automation:
- Makefile for standardized commands
- Bootstrap script for creating labs
- Testing framework

See [Phase 2: Automation](phase2-automation.md)