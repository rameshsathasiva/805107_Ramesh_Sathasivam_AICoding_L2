# Customer 360 Data Pipeline

## Project Overview

This project builds a Customer 360 data pipeline that ingests customer, order, and support-ticket data, cleans and standardizes it, joins the sources into a customer-level dataset, and exports a set of CSV outputs for analysis. The workflow is implemented in Python and includes unit tests and a Streamlit-based dashboard for viewing the final customer dataset.

## Folder Structure

- data/ - Source Excel files for customers, orders, and support tickets
- outputs/ - Generated CSV outputs from the pipeline
- src/ - Pipeline code and Streamlit app entry points
  - src/starter_pipeline.py - Main data processing workflow
  - src/pipeline.py - Thin wrapper for running the pipeline
  - src/customer_360_app.py - Streamlit app for exploring the Customer 360 dataset
- tests/ - Pytest-based unit tests for data cleaning and aggregation logic

## Setup Instructions

Create and activate a virtual environment, then install the required dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to Run the Data Pipeline

Run the pipeline from the repository root:

```bash
python src/pipeline.py
```

This will generate the following files in the outputs folder:

- outputs/customer_360.csv
- outputs/kpi_summary.csv
- outputs/region_revenue.csv
- outputs/category_revenue.csv
- outputs/data_quality_report.csv

## How to Run the Pytest Suite

Run the unit tests with:

```bash
pytest -q tests/test_pipeline.py
```

## How to Launch the Streamlit App

Start the Streamlit dashboard from the repository root:

```bash
streamlit run src/customer_360_app.py
```

The app will load the generated Customer 360 CSV from the outputs folder and display the data for exploration.