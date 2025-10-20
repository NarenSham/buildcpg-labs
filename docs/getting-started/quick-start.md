# Quick Start Guide

Get up and running with BuildCPG Labs in 10 minutes.

## Prerequisites

- Python 3.11+
- Mac 11+ or Linux
- Git
- Basic terminal knowledge

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/narensham/buildcpg-labs.git
cd buildcpg-labs
```

### 2. Install Dependencies
```bash
pip install pyyaml duckdb pandas
```

### 3. Verify Setup
```bash
python config/paths.py
# Output: ✅ Lab1 config loaded: ...
```

## Your First Lab Run

### Setup Lab1 (One Time)
```bash
cd lab1_sales_performance
make setup
# Creates venv, installs dependencies, runs dbt debug
```

### Run the Pipeline
```bash
make run
# Executes: dbt run
```

### Inspect Your Data
```bash
make inspect
# Shows: schemas, tables, row counts, quality scores
```

### Run Tests
```bash
make test
# Executes: dbt test
```

## Create a New Lab

### Bootstrap Lab2
```bash
cd ..
./setup_new_lab.sh lab2_forecast_model
```

### Use Lab2 Immediately
```bash
cd lab2_forecast_model
make run
```

## Common Commands

### Working on Lab1
```bash
cd lab1_sales_performance

make setup      # Initialize lab (one time)
make run        # Run dbt pipeline
make test       # Run dbt tests
make inspect    # Check data quality
make clean      # Clean build artifacts
make docs       # Generate dbt documentation
```

### Across All Labs
```bash
# Check all labs
ls -la | grep lab

# Status of each lab
cat config/labs_config.yaml

# Check paths
python config/paths.py
```

## What Happened?

When you ran `make setup` in lab1:

1. **Created venv** - Isolated Python environment
2. **Installed dependencies** - From requirements.txt
3. **Ran dbt debug** - Verified dbt setup

When you ran `make run`:

1. **Activated venv** - Automatically (no need for `source venv/bin/activate`)
2. **Changed to dbt directory** - `cd dbt`
3. **Ran dbt run** - Executed transformation pipeline
4. **Created/updated tables** - In DuckDB database

When you ran `make inspect`:

1. **Connected to database** - lab1_sales_performance.duckdb
2. **Listed all schemas** - raw, raw_bronze, raw_gold, raw_silver
3. **Showed table stats** - Row counts, column counts
4. **Calculated quality** - Checked for nulls, duplicates

## Next Steps

- Read [Lab Structure](../labs/lab-structure.md) to understand directory layout
- Read [Shared vs Lab-Specific](../architecture/shared-vs-lab-specific.md) to understand how code is organized
- Read [Creating New Lab](../labs/creating-new-lab.md) for detailed lab creation guide
- Read [Troubleshooting](../troubleshooting.md) if you hit any issues

## Troubleshooting

### "command not found: make"
You need to install `make`. On Mac:
```bash
xcode-select --install
```

### "venv not found"
Run `make setup` first to create the virtual environment.

### "dbt: command not found"
Make sure you ran `make setup` to install dbt in the venv.

For more help, see [Troubleshooting](../troubleshooting.md).