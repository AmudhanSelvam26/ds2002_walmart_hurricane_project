# DS2002 Midterm — Walmart Hurricane Analytics

Team notebook: `notebooks/team_notebook.ipynb`.

The notebook finds the repo root by looking for `data/walmart_transactions.csv`, then runs `src/clean_pipeline.py` and `src/build_sku_mapping.py` before the analysis cells. Open it from anywhere inside this repo.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
jupyter lab notebooks/team_notebook.ipynb
```

In Jupyter, use the `.venv` kernel, then choose **Restart Kernel and Run All Cells**.

## Data the notebook expects

These files are already in the repo:

- `data/walmart_transactions.csv`
- `data/store_locations.csv`
- `data/product_catalog.csv`
- `data/inventory_and_sales.db`

Cleaning writes `data/processed/`. Question 3 reads `data/processed/weather_daily_open_meteo.csv` when that file exists. If it does not, the notebook calls the Open-Meteo archive API and needs a network connection:

https://archive-api.open-meteo.com/v1/archive
