#!/bin/bash
echo "Setting up buildcpg-labs local environment..."

python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p shared/{utils,configs,metadata}
mkdir -p lab1_sales_performance/{data,etl,dbt,bi,docs}

echo "✅ Environment setup complete! Activate it with: source venv/bin/activate"
