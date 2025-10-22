# Architecture Overview

## System Design

BuildCPG Labs uses a **multi-lab, shared-utilities** architecture designed for scalability and independence.

```
┌─────────────────────────────────────────────────────────┐
│         ORCHESTRATION LAYER (Airflow/Prefect)           │
│  Schedules pipelines, monitors health, handles alerts   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              DATA INGESTION LAYER                        │
│  • CSV monitoring • API polling • Data validation       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│         dbt TRANSFORMATION LAYER (Per Lab)              │
│  • Bronze (Raw) → Silver (Cleaned) → Gold (Analytics)  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              QUALITY ASSURANCE LAYER                     │
│  • dbt tests • Data freshness • Quality scoring         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│         SHARED UTILITIES LAYER (Root Level)             │
│  • DataInspector • CSVMonitor • Path Helpers            │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure (Current Setup)

```
buildcpg-labs/
│
├── .venv/                           # SINGLE venv (shared by all labs)
│   ├── bin/
│   ├── lib/
│   └── ...
│
├── shared/                          # Shared across ALL labs
│   ├── __init__.py
│   ├── utils/
│   │   ├── data_inspector.py       # Inspect databases
│   │   ├── csv_monitor.py          # Detect new data
│   │   └── config_loader.py        # Load configurations
│   │
│   ├── config/                      # Config inside shared (not at root)
│   │   ├── labs_config.yaml        # Central lab registry
│   │   └── paths.py                # Path helpers
│   │
│   ├── data_quality/
│   │   ├── validators.py           # Quality validators
│   │   └── expectations.py         # Data expectations
│   │
│   └── templates/
│       ├── Makefile_template       # Template Makefile
│       ├── requirements_template.txt
│       ├── dbt_project_template.yml
│       └── .gitignore_template
│
├── lab1_sales_performance/         # LAB 1 (Independent data, shares venv)
│   ├── dbt/
│   │   ├── dbt_project.yml
│   │   ├── profiles.yml            # Manually edited when switching labs
│   │   ├── models/
│   │   │   ├── staging/
│   │   │   ├── intermediate/
│   │   │   └── marts/
│   │   └── tests/
│   │
│   ├── data/
│   │   ├── raw/
│   │   └── lab1_sales_performance.duckdb
│   │
│   ├── scripts/
│   │   ├── inspect_data.py
│   │   └── check_for_new_data.py
│   │
│   ├── pipelines/
│   │   ├── data_ingestion.py
│   │   └── data_quality.py
│   │
│   ├── requirements.txt            # Shared dependencies
│   └── .gitignore
│
├── lab2_forecast_model/            # LAB 2 (Independent data, shares venv)
│   └── (Same structure as lab1)
│
├── lab3_customer_segmentation/     # LAB 3 (Independent data, shares venv)
│   └── (Same structure as lab1)
│
├── orchestration/
│   └── airflow_dags.py             # Multi-lab orchestration
│
├── docs/                           # This documentation
├── setup_new_lab.sh                # Bootstrap new labs
├── mkdocs.yml                      # Documentation config
├── .gitignore
└── README.md
```

## Key Concepts

### Single Virtual Environment Approach

**Current Setup:**
- ONE `.venv/` at root shared by all labs
- All labs use same Python packages
- Switch between labs by changing dbt profiles manually

**Advantages:**
- Less disk space (~500MB vs ~500MB per lab)
- Consistent package versions across all labs
- Simpler initial setup

**Trade-offs:**
- Cannot have labs with conflicting dependencies
- Must manually edit `profiles.yml` when switching labs
- Risk of profile switching errors (writing to wrong database)
- No concurrent work on different labs

⚠️ **See [Current Setup Details](current-setup.md) for full pros/cons analysis**

### Labs Have Independent Data
- Each lab has its own **database** (lab1.duckdb, lab2.duckdb)
- Each lab has its own **dbt project** (dbt/models/, dbt/dbt_project.yml)
- Each lab has its own **raw data** (data/raw/)
- Labs share Python environment but NOT data

### Shared Utilities
- **DataInspector** - Check database quality (used by all labs)
- **CSVMonitor** - Detect new data in CSVs (used by all labs)
- **Config Paths** - Get paths for any lab (used by all labs)
- Written once in `shared/`, used by all labs
- Bug fix in shared code fixes all labs

### Configuration Location

**Config is inside shared/config/ (not at root level):**

```python
# Import pattern for lab scripts
import sys
sys.path.insert(0, '../..')
from shared.config.paths import get_lab_db_path  # Note: shared.config

# NOT this:
# from config.paths import get_lab_db_path  # ❌ Wrong path
```

```yaml
# shared/config/labs_config.yaml
labs:
  lab1_sales_performance:
    path: lab1_sales_performance
    db_path: lab1_sales_performance/data/lab1_sales_performance.duckdb
    dbt_path: lab1_sales_performance/dbt
    
  lab2_forecast_model:
    path: lab2_forecast_model
    db_path: lab2_forecast_model/data/lab2_forecast_model.duckdb
    dbt_path: lab2_forecast_model/dbt
```

This registry tells the system where each lab is and how to find its resources.

## Data Flow

### Single Lab Example
```
CSV Input
    ↓
dbt Load (raw schema)
    ↓
dbt Transform (bronze → silver → gold)
    ↓
DuckDB Tables
    ↓
DataInspector (quality check)
    ↓
BI Tool (Tableau/Looker)
```

### Multiple Labs Orchestrated
```
Airflow DAG (Daily 12 AM)
    ├── Lab1: Check CSV → Load → Transform → Test → Inspect
    ├── Lab2: Check CSV → Load → Transform → Test → Inspect
    └── Lab3: Check CSV → Load → Transform → Test → Inspect
    ↓
All results aggregated
    ↓
Alert team if any lab fails
```

## Workflow: Switching Between Labs

```bash
# 1. Activate shared venv (once per session)
cd buildcpg-labs
source .venv/bin/activate

# 2. Work on lab1
cd lab1_sales_performance/dbt
# profiles.yml should point to: ../data/lab1_sales_performance.duckdb
dbt debug  # Verify correct database
dbt run

# 3. Switch to lab2
cd ../../lab2_forecast_model/dbt
# Edit profiles.yml to point to: ../data/lab2_forecast_model.duckdb
vim profiles.yml  # Update path
dbt debug  # Verify correct database
dbt run
```

⚠️ **Critical:** Always run `dbt debug` before `dbt run` to verify you're pointing to the correct database.

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Database** | DuckDB (embedded, Mac compatible) |
| **Transformation** | dbt (data build tool) |
| **Scripting** | Python 3.11+ |
| **Environment** | Single venv (shared) |
| **Orchestration** | Airflow (optional, future) |
| **Version Control** | Git |
| **Documentation** | MkDocs |

## Design Principles

### 1. Data Independence
Labs have separate databases and raw data. One lab's data corruption doesn't affect others.

### 2. Shared Python Environment
All labs use same venv for consistency and space efficiency (with trade-offs).

### 3. Reusability
Code written for shared utilities is used by all labs without duplication.

### 4. Scalability
Adding lab 10 takes same effort as adding lab 2 (but dependency conflicts may limit this).

### 5. Clarity
Each lab's purpose is clear. Shared code's purpose is clear.

### 6. Manual Coordination
Profile switching requires discipline and verification steps.

## Comparison: Current vs Alternative Architectures

### Current Setup (Single venv)
✅ Space efficient (one venv)  
✅ Consistent packages  
✅ Simple setup  
❌ Dependency conflicts possible  
❌ Manual profile switching  
❌ No concurrent work  

### Alternative: Per-Lab venvs
❌ More disk space  
❌ More complex setup  
✅ Complete isolation  
✅ Different dependencies per lab  
✅ Automatic profile management  
✅ Concurrent work safe  

**When to migrate:** See [Current Setup Analysis](current-setup.md)

## Migration Path

### Current State: Phase 1 (Single venv)
- Shared utilities ✅
- Central configuration ✅
- Lab1 working ✅
- Single venv ✅

### Future: Phase 2 (Optional migration to per-lab venvs)
When you hit:
- 3+ labs
- Dependency conflicts
- Multiple team members
- Production requirements

Then consider: Per-lab venvs + automated profile management

---

## See Also

- **[Current Setup Details](current-setup.md)** - Full analysis of single venv approach
- **[Shared vs Lab-Specific](shared-vs-lab-specific.md)** - What goes where
- **[Phase 1 Guide](../phases/phase1-foundation.md)** - Implementation details