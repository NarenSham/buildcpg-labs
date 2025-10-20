# Frequently Asked Questions

## General Questions

### What is BuildCPG Labs?
A data engineering platform for managing multiple independent data labs using dbt, DuckDB, and Python. Each lab is isolated but shares common utilities.

### Why multiple labs instead of one big project?
Different labs often have:
- Different data sources and formats
- Different transformation logic
- Different schedules and SLAs
- Independent teams working on them

Keeping them separate prevents one from breaking others.

### Do I need to use all labs?
No. You can start with lab1 and create additional labs as needed. Each lab works independently.

### Can labs share data?
Currently, each lab has its own database. Future versions will support lab-to-lab data sharing through view exports.

### Does this work on Windows?
Yes, with WSL2 (Windows Subsystem for Linux). Mac 11+ and Linux are natively supported. No Docker required.

## Architecture Questions

### Why DuckDB instead of other databases?
- No server needed (embedded)
- Works on older Macs (Mac 11+)
- No Docker required
- Small, easy to manage
- Perfect for single-machine setups
- Can scale to multi-machine later

### What's the difference between shared and lab-specific files?
**Shared:** Code used by ALL labs (DataInspector, CSVMonitor)  
**Lab-specific:** Code only that lab uses (models, dashboards, data)

### How do labs communicate?
They don't (by design). Future phases will add data export/import between labs.

### Can I use different Python versions per lab?
Yes. Each lab has its own venv, so different packages/versions are allowed.

## Setup Questions

### How long does setup take?
- **First time:** 10-15 minutes (download, install dependencies)
- **Each additional lab:** 2 minutes (automatic bootstrap)

### Can I skip Phase 1?
Not recommended. Phase 1 creates the foundation that Phases 2+ depend on.

### What if I only want Phase 1?
That's fine. Phase 1 is fully functional for basic lab work. Phase 2 adds convenience but isn't required.

### Can I customize the templates?
Yes. Edit files in `shared/templates/` and they'll be used for new labs created after that.

## Usage Questions

### What does `make setup` do?
1. Creates Python virtual environment (venv)
2. Installs dependencies from requirements.txt
3. Runs dbt debug to verify setup

### What does `make run` do?
Executes `dbt run` which transforms data through bronze → silver → gold layers.

### How do I see what changed in my database?
Run `make inspect` to see schemas, tables, row counts, and quality scores.

### Can I use dbt commands directly?
Yes. `cd lab/dbt && dbt run` works the same as `make run`. Makefile just automates activation.

### How do I add a new model to lab1?
```bash
cd lab1_sales_performance/dbt/models
# Create .sql file
# Run: make run
```

See dbt documentation for model details.

## Shared Utilities Questions

### How do I use DataInspector in my code?
```python
import sys
sys.path.insert(0, '../..')
from shared.utils.data_inspector import DataInspector

inspector = DataInspector('data/lab1_sales_performance.duckdb')
schemas = inspector.get_all_schemas()
```

### Can I modify shared utilities?
Yes, but test thoroughly. Changes affect ALL labs.

### How do I add a new shared utility?
1. Create file in `shared/utils/`
2. Import it in your lab scripts
3. Test thoroughly
4. Commit to git

### Do shared utilities get committed to git?
Yes. They're in the git repo so everyone gets them.

## Data Questions

### Where is my data stored?
In `lab/data/lab_name.duckdb` (DuckDB database file).

### How do I backup my data?
```bash
# Simply copy the .duckdb file
cp lab1_sales_performance/data/lab1_sales_performance.duckdb lab1_sales_performance/data/lab1_sales_performance.duckdb.backup
```

### How large can databases get?
DuckDB on a single machine can handle multi-GB databases easily. For 100GB+, consider upgrading infrastructure.

### Can I read external data in dbt?
Yes. dbt supports reading from CSVs, APIs, and other sources via Jinja2 macros.

### How do I connect to real databases (not DuckDB)?
Future versions will support PostgreSQL, MySQL, etc. Currently limited to DuckDB.

## Git Questions

### Can I commit my venv?
No. It's huge and system-specific. Use `.gitignore` to exclude it.

### Can I commit my .duckdb files?
For development: no (they change constantly).  
For tracked data: yes (if you need version history).

### How do I prevent accidental commits?
`.gitignore` automatically excludes venv, .duckdb, and build artifacts.

### What should I commit?
- dbt models (.sql files)
- Python scripts (.py files)
- Configuration files (.yml, .yaml)
- Documentation (.md files)
- requirements.txt

### What shouldn't I commit?
- venv/ directories
- .duckdb files (unless intentional)
- dbt/target/ and dbt/logs/
- .DS_Store
- IDE settings

## Performance Questions

### How fast does dbt run?
Depends on data size. With ~3K rows: 1-2 seconds. Scale linearly with data.

### Can I make dbt faster?
- Incremental materialization (load only new data)
- Optimize SQL queries
- Add indexes (if using real databases)

### Will my laptop slow down with multiple labs?
Each lab runs independently. Multiple venvs take ~500MB each. Not a concern for 10 labs.

## Scaling Questions

### Can I scale to 50 labs?
Yes. Structure supports unlimited labs. You'll just need:
- Disk space (~1GB per lab average)
- Orchestration tool (Airflow) to manage all runs

### What's the limit?
No hard limit. Practical limit depends on infrastructure.

### Can I migrate to cloud later?
Yes. The architecture is platform-agnostic. Move to Snowflake/BigQuery/etc. when needed.

## Phase Questions

### What's the difference between phases?
- **Phase 1:** Shared utilities + configuration
- **Phase 2:** Makefile + bootstrap (automation)
- **Phase 3+:** Orchestration + monitoring

### Can I use Phase 1 without Phase 2?
Yes. Phase 1 is standalone and functional.

### When should I use Phase 2?
When you want `make` commands and automated lab creation. Highly recommended.

### When should I use Phase 3?
When managing 3+ labs and want automated scheduling (Airflow).

## Team Questions

### Can multiple people work on same lab?
Yes. Use git branches for features.

### Can different people own different labs?
Yes. Each lab is independent.

### How do we prevent conflicts?
- Use git for coordination
- Clear lab ownership
- Communication on shared utilities

### Can we code review lab changes?
Yes. Pull requests work for both lab-specific and shared code.

## Troubleshooting Questions

### My database is corrupted
```bash
# Delete it and recreate
rm lab1_sales_performance/data/lab1_sales_performance.duckdb
cd lab1_sales_performance/dbt
dbt run  # Recreates from source
```

### I accidentally deleted a model
```bash
git checkout <file>  # Restore from git
cd dbt
dbt run  # Recreate tables
```

### Everything is broken
```bash
git status  # See what changed
git diff   # See details
git reset --hard  # Go back to last commit
```

### Who do I ask for help?
See [Troubleshooting](troubleshooting.md) guide or ask maintainer.

## Feature Questions

### Can I add monitoring/alerting?
Yes, in Phase 3+. Currently manual checks only.

### Can I use Python notebooks?
Yes. Put them in `lab/notebooks/`.

### Can I have dashboards?
Yes. Connect BI tools (Tableau/Looker) to lab databases.

### Can I do ML?
Yes. Add models to `lab/pipelines/` or use Jupyter.

---

## Still Have Questions?

- Check [Getting Started](getting-started/quick-start.md)
- Check [Troubleshooting](troubleshooting.md)
- Check [Architecture](architecture/overview.md)
- Ask in GitHub Issues