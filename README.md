A modern, scalable data engineering platform for managing multiple independent labs using dbt, DuckDB, and Python.

[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://buildcpg-labs.github.io)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick Links

- ** [Quick Start](docs/getting-started/quick-start.md)** - Get running in 10 minutes
- ** [Architecture](docs/architecture/overview.md)** - Understand the design
- ** [FAQ](docs/faq.md)** - Common questions answered
- ** [Troubleshooting](docs/troubleshooting.md)** - Fix common issues

## What This Is

BuildCPG Labs lets you:

✅ **Run multiple independent data labs** - Each with its own database, code, and configuration  
✅ **Share reusable utilities** - DataInspector, CSVMonitor, validators across all labs  
✅ **Use consistent commands** - `make run`, `make test`, `make inspect` for any lab  
✅ **Create new labs instantly** - `./setup_new_lab.sh lab_name` in 2 minutes  
✅ **Scale without complexity** - Go from 1 lab to 100 with the same structure  
✅ **No Docker required** - Works on Mac 11+, Linux, no containers needed  

## Architecture

```
buildcpg-labs/
├── shared/                   # Reusable utilities (ALL labs use this)
│   ├── utils/               # DataInspector, CSVMonitor, config loaders
│   └── templates/           # Templates for new labs
├── config/                  # Central configuration
│   ├── labs_config.yaml     # Registry of all labs
│   └── paths.py             # Path helpers
├── lab1_sales_performance/  # LAB 1 (independent)
├── lab2_forecast_model/     # LAB 2 (independent)
└── lab3.../                 # LAB N (independent)
```

## Getting Started

### Prerequisites

```bash
# Python 3.11+
python --version

# Git
git --version

# Make (for Makefile commands)
make --version
```

### Installation (5 minutes)

```bash
# 1. Clone
git clone https://github.com/narensham/buildcpg-labs.git
cd buildcpg-labs

# 2. Install dependencies
pip install pyyaml duckdb pandas

# 3. Verify
python config/paths.py
# ✅ Lab1 config loaded

# 4. Setup lab1
cd lab1_sales_performance
make setup

# 5. Run pipeline
make run

# 6. Inspect data
make inspect
```

That's it! You're ready.

## Common Commands

### Work on Lab 1

```bash
cd lab1_sales_performance

make setup      # Initialize lab (one time)
make run        # Run dbt pipeline
make test       # Run dbt tests
make inspect    # Check data quality
make clean      # Clean build artifacts
```

### Create New Lab

```bash
cd ..
./setup_new_lab.sh lab2_forecast_model
cd lab2_forecast_model
make run
```

## Project Structure

```
├── shared/
│   ├── utils/
│   │   ├── data_inspector.py    # Inspect any lab's database
│   │   ├── csv_monitor.py       # Detect new data
│   │   └── config_loader.py     # Access lab config
│   └── templates/
│       ├── Makefile             # Template for new labs
│       └── requirements.txt
│
├── config/
│   ├── labs_config.yaml         # All labs registered here
│   └── paths.py                 # Get paths to any lab
│
├── lab1_sales_performance/      # Lab 1 (complete example)
│   ├── dbt/                     # dbt project
│   ├── data/                    # Database and raw data
│   ├── scripts/                 # Inspection scripts
│   ├── pipelines/               # Data pipelines
│   ├── Makefile                 # Lab commands
│   ├── requirements.txt         # Python dependencies
│   └── venv/                    # Virtual environment
│
├── lab2_forecast_model/         # Lab 2 (template)
├── lab3.../                     # Lab 3 (template)
│
├── setup_new_lab.sh             # Bootstrap script
├── mkdocs.yml                   # Documentation config
├── .gitignore                   # Git configuration
└── README.md                    # This file
```

## Phases

### Phase 1: Foundation ✅
- Shared utilities (DataInspector, CSVMonitor)
- Central configuration
- Lab1 ready to use

### Phase 2: Automation (Ready)
- Makefile templates
- Bootstrap script for new labs
- Automated setup

### Phase 3+: Future
- Orchestration (Airflow/Prefect)
- Advanced monitoring
- Data quality gates
- Multi-database support

## Key Features

### Shared Utilities

Written once in `shared/`, used by all labs:

```python
# DataInspector - inspect any database
from shared.utils.data_inspector import DataInspector

inspector = DataInspector('data/lab1_sales_performance.duckdb')
quality_score = inspector.get_quality_score('gold', 'summary')
```

### Central Configuration

All labs registered in one place:

```yaml
# config/labs_config.yaml
labs:
  lab1_sales_performance:
    path: lab1_sales_performance
    db_path: lab1_sales_performance/data/lab1_sales_performance.duckdb
    
  lab2_forecast_model:
    path: lab2_forecast_model
    db_path: lab2_forecast_model/data/lab2_forecast_model.duckdb
```

### Standardized Commands

Every lab uses the same Makefile:

```bash
make setup      # Works for any lab
make run        # Works for any lab
make test       # Works for any lab
```

## Example: End-to-End

```bash
# 1. Create lab2
./setup_new_lab.sh lab2_forecast_model

# 2. Work on it
cd lab2_forecast_model
make run
make inspect

# 3. Create lab3
cd ..
./setup_new_lab.sh lab3_customer_segmentation

# 4. Run all labs at once (Airflow will do this)
for lab in lab1_sales_performance lab2_forecast_model lab3_customer_segmentation; do
  cd $lab
  make run
  make test
  cd ..
done
```

## Documentation

Full documentation is available at: **https://buildcpg-labs.github.io**

### Key Guides

- [Quick Start](docs/getting-started/quick-start.md) - 10-minute setup
- [Installation](docs/getting-started/installation.md) - Detailed installation
- [Architecture](docs/architecture/overview.md) - System design
- [Multi-Lab Design](docs/architecture/multi-lab-design.md) - How labs work together
- [Phase 1](docs/phases/phase1-foundation.md) - Foundation setup
- [Troubleshooting](docs/troubleshooting.md) - Common issues
- [FAQ](docs/faq.md) - Frequently asked questions

## Technology Stack

- **Python** 3.11+ - Scripting and tooling
- **dbt** - Data transformation
- **DuckDB** - Embedded database (no server needed)
- **MkDocs** - Documentation
- **Git** - Version control
- **Make** - Command automation

## Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.11 | 3.12+ |
| OS | Mac 11+ / Linux | Mac 12+ / Ubuntu 20.04+ |
| Disk | 1GB | 10GB |
| RAM | 2GB | 4GB+ |
| Docker | Not needed ✅ | Not needed ✅ |

## Installation Methods

### Method 1: Manual (Recommended)
```bash
git clone https://github.com/narensham/buildcpg-labs.git
cd buildcpg-labs
pip install pyyaml duckdb pandas
python config/paths.py
```

### Method 2: Automated Setup
```bash
git clone https://github.com/narensham/buildcpg-labs.git
cd buildcpg-labs
chmod +x setup.sh
./setup.sh
```

See [Installation Guide](docs/getting-started/installation.md) for detailed instructions.

## Next Steps

1. **[Quick Start](docs/getting-started/quick-start.md)** - Setup and run in 10 minutes
2. **[Architecture](docs/architecture/overview.md)** - Understand the design
3. **[Create New Lab](docs/labs/creating-new-lab.md)** - Add your own lab
4. **[Troubleshooting](docs/troubleshooting.md)** - Fix issues

## Support

- 📖 **[Read the docs](https://buildcpg-labs.github.io)**
- ❓ **[Check FAQ](docs/faq.md)**
- 🔧 **[Troubleshooting](docs/troubleshooting.md)**
- 💬 **[GitHub Issues](https://github.com/narensham/buildcpg-labs/issues)**

## Contributing

Contributions welcome! See [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Created by:** narensham  
**Last Updated:** January 2025  
**Repository:** [GitHub](https://github.com/narensham/buildcpg-labs)  
**Documentation:** [MkDocs](https://buildcpg-labs.github.io)