.PHONY: help setup install dbt-run dbt-test mlflow-ui train serve docs serve-docs test

help:
	@echo "make setup    -> create venv and install deps"
	@echo "make dbt-run  -> run dbt models"
	@echo "make mlflow   -> start mlflow ui"
	@echo "make train    -> run training script"
	@echo "make serve    -> start gradio app"
	@echo "make docs     -> build docs"
	@echo "make test     -> run pytest"

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

dbt-run:
	dbt run --profiles-dir .

dbt-test:
	dbt test --profiles-dir .

mlflow:
	mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns

train:
	python src/models/train_model.py

serve:
	python src/serve/gradio_app.py

docs:
	mkdocs build

test:
	pytest -q
