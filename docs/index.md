# BuildCPG Labs

A modern, scalable data engineering platform for managing multiple independent labs using dbt, DuckDB, and Python.

## Overview

BuildCPG Labs enables you to:

- **Run independent labs** - Each lab has its own database, code, and configuration
- **Share utilities** - Common code used by all labs without duplication
- **Scale easily** - Create new labs in minutes with automation
- **Maintain quality** - Built-in data inspection and quality checks
- **Automate workflows** - Orchestrate multiple labs with a single command

## Key Features

### Multi-Lab Architecture
Each lab is completely independent but shares common utilities:
```
buildcpg-labs/
├── shared/           # Reusable utilities (used by ALL labs)
├── config/           # Central configuration
├── lab1_sales_performance/  # Lab 1 (independent)
├── lab2_forecast_model/     # Lab 2 (independent)
└── lab3_customer_segmentation/ # Lab 3 (independent)
```

### Standard Commands
Work with any lab using consistent Makefile commands:
```bash
make setup      # Initialize lab
make run        # Run dbt pipeline
make test       # Run tests
make inspect    # Check data quality
```

### Easy Lab Creation
Bootstrap new labs automatically:
```bash
./setup_new_lab.sh lab4_churn_prediction
```

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/narensham/buildcpg-labs.git
cd buildcpg-labs
```

### 2. Work with Lab 1
```bash
cd lab1_sales_performance
make setup
make run
make inspect
```

### 3. Create Lab 2
```bash
cd ..
./setup_new_lab.sh lab2_forecast_model
cd lab2_forecast_model
make run
```

## Documentation Structure

- **[Getting Started](getting-started/quick-start.md)** - Setup and first steps
- **[Architecture](architecture/overview.md)** - Design and concepts
- **[Phases](phases/phase1-foundation.md)** - Implementation phases
- **[Labs Guide](labs/using-makefile.md)** - Working with labs
- **[Utilities](utilities/data-inspector.md)** - Shared tools reference
- **[Troubleshooting](troubleshooting.md)** - Common issues and fixes

## Project Status

### Phase 1: Foundation ✅
- Shared utilities (DataInspector, CSVMonitor)
- Central configuration registry
- Lab1 inspection scripts

### Phase 2: Automation (In Progress)
- Makefile templates
- Bootstrap script
- Lab1 working setup

### Phase 3+: Future
- Orchestration (Airflow/Prefect)
- Advanced monitoring
- Data quality gates

## Requirements

- Python 3.11+
- Mac 11+ (no Docker)
- Git

## Support

See [Troubleshooting](troubleshooting.md) or [FAQ](faq.md) for common issues.

---

**Last Updated:** January 2025  
**Maintainer:** narensham  
**Repository:** [GitHub](https://github.com/narensham/buildcpg-labs)