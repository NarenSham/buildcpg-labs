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

## Directory Structure

```
buildcpg-labs/
│
├── shared/                          # Shared across ALL labs
│   ├── __init__.py
│   ├── utils/
│   │   ├── data_inspector.py       # Inspect databases
│   │   ├── csv_monitor.py          # Detect new data
│   │   └── config_loader.py        # Load configurations
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
├── config/
│   ├── labs_config.yaml            # Central lab registry
│   └── paths.py                    # Path helpers
│
├── lab1_sales_performance/         # LAB 1 (Independent)
│   ├── dbt/
│   │   ├── dbt_project.yml
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
│   ├── Makefile
│   ├── requirements.txt
│   ├── venv/
│   └── .gitignore
│
├── lab2_forecast_model/            # LAB 2 (Independent)
│   └── (Same structure as lab1)
│
├── lab3_customer_segmentation/     # LAB 3 (Independent)
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

### Labs Are Independent
- Each lab has its own **database** (lab1.duckdb, lab2.duckdb)
- Each lab has its own **dbt project** (dbt/models/, dbt/dbt_project.yml)
- Each lab has its own **Python environment** (venv/)
- Each lab can use different versions of packages
- Labs don't affect each other if one breaks

### Shared Utilities
- **DataInspector** - Check database quality (used by all labs)
- **CSVMonitor** - Detect new data in CSVs (used by all labs)
- **Config Paths** - Get paths for any lab (used by all labs)
- Written once, used by all labs
- Bug fix in shared code fixes all labs

### Central Configuration
```yaml
# config/labs_config.yaml
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

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Database** | DuckDB (embedded, Mac compatible) |
| **Transformation** | dbt (data build tool) |
| **Scripting** | Python 3.11+ |
| **Orchestration** | Airflow (optional) |
| **Version Control** | Git |
| **Documentation** | MkDocs |

## Design Principles

### 1. Independence
Labs can fail independently. One broken lab doesn't affect others.

### 2. Reusability
Code written for shared utilities is used by all labs without duplication.

### 3. Scalability
Adding lab 10 takes same effort as adding lab 2.

### 4. Clarity
Each lab's purpose is clear. Shared code's purpose is clear.

### 5. Automation
Manual work is minimized. Bootstrapping and Makefiles handle repetition.

## Comparison: Before vs After

### Before (Before Phase 1)
- Everything in root or lab1
- Duplicate code across potential labs
- Manual setup for each lab
- Unclear structure
- Hard to add new labs

### After Phase 1 (Foundation)
- Clear shared vs lab-specific separation
- Reusable utilities
- Still manual setup
- But clear structure ready for automation

### After Phase 2 (Automation)
- `make` commands everywhere
- `./setup_new_lab.sh` creates labs instantly
- Everything documented
- Scaling is trivial

---

See [Multi-Lab Design](multi-lab-design.md) for detailed explanation of how labs interact.