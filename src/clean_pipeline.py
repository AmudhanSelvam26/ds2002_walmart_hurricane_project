"""Reproducible Walmart hurricane cleaning pipeline.

Run from anywhere: python src/clean_pipeline.py
Input: data/walmart_transactions.csv, data/store_locations.csv
Outputs: data/processed/*.csv

Policy: negative quantities are quarantined as potential returns, not counted
as positive demand. Review this policy with the team's cleaning owner.
"""
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data'
OUT = RAW / 'processed'


def normalize_store_id(value):
    if pd.isna(value):
        return pd.NA
    s = re.sub(r'[\s_-]', '', str(value).upper())
    if re.fullmatch(r'FL\d+', s):
        return 'FL-' + s[2:]
    return s or pd.NA


def log_event(log, action, affected, removed, explanation):
    log.append(dict(action=action, rows_affected=int(affected),
                    rows_removed=int(removed), explanation=explanation))


def clean_stores(df, log):
    stores = df.copy()
    stores.columns = stores.columns.str.strip()
    required = {'store_id', 'latitude', 'longitude'}
    if not required.issubset(stores.columns):
        raise ValueError(f'Store file missing columns: {required - set(stores.columns)}')
    before = stores['store_id'].copy()
    stores['store_id'] = stores['store_id'].map(normalize_store_id)
    log_event(log, 'Normalize store IDs in lookup', (before.astype('string') != stores['store_id'].astype('string')).fillna(False).sum(), 0,
              'Standardize FL239, FL_239, fl-239 to FL-239')
    dupes = stores.duplicated(subset='store_id', keep='first')
    log_event(log, 'Deduplicate store lookup', dupes.sum(), dupes.sum(), 'Keep first row for each canonical store ID')
    stores = stores.loc[~dupes].copy()
    stores['latitude'] = pd.to_numeric(stores['latitude'], errors='coerce')
    stores['longitude'] = pd.to_numeric(stores['longitude'], errors='coerce')
    stores['state'] = stores['state'].astype('string').str.strip().replace({'Florida':'FL', 'Fla.':'FL'}) if 'state' in stores else 'FL'
    log_event(log, 'Flag missing coordinates', stores[['latitude','longitude']].isna().any(axis=1).sum(), 0,
              'Keep stores with missing coordinates; geocode separately for weather')
    return stores.reset_index(drop=True)


def clean_transactions(df, stores, log):
    sales = df.copy()
    sales.columns = sales.columns.str.strip()
    required = {'timestamp', 'store_id', 'quantity', 'unit_price'}
    if not required.issubset(sales.columns):
        raise ValueError(f'Transactions missing columns: {required - set(sales.columns)}')
    raw_rows = len(sales)
    dupes = sales.duplicated(keep='first')
    log_event(log, 'Drop exact duplicate transaction rows', dupes.sum(), dupes.sum(),
              'Potential duplicate exports; confirm this policy if identical purchases may be legitimate')
    sales = sales.loc[~dupes].copy()
    old_ids = sales['store_id'].astype('string')
    sales['store_id'] = sales['store_id'].map(normalize_store_id)
    log_event(log, 'Normalize transaction store IDs', (old_ids != sales['store_id'].astype('string')).fillna(False).sum(), 0,
              'Match canonical IDs in store lookup')

    # Parse heterogeneous timestamp strings as local Eastern wall-clock time.
    sales['timestamp'] = pd.to_datetime(sales['timestamp'], errors='coerce', format='mixed')
    bad_time = sales['timestamp'].isna()
    log_event(log, 'Remove invalid/missing timestamps', bad_time.sum(), bad_time.sum(),
              'Unusable for daily hurricane analysis')
    sales = sales.loc[~bad_time].copy()

    price_raw = sales['unit_price'].astype('string').str.replace(r'[$,\s]', '', regex=True)
    sales['unit_price'] = pd.to_numeric(price_raw, errors='coerce')
    invalid_price = sales['unit_price'].isna() | (sales['unit_price'] < 0)
    log_event(log, 'Quarantine missing/invalid prices', invalid_price.sum(), invalid_price.sum(),
              'Do not silently convert missing, text, or negative unit prices to zero')
    price_rejected = sales.loc[invalid_price].copy()
    sales = sales.loc[~invalid_price].copy()

    sales['quantity'] = pd.to_numeric(sales['quantity'], errors='coerce')
    invalid_qty = sales['quantity'].isna() | (sales['quantity'] == 0)
    log_event(log, 'Quarantine missing/zero quantities', invalid_qty.sum(), invalid_qty.sum(),
              'No usable positive unit volume')
    qty_rejected = sales.loc[invalid_qty].copy()
    sales = sales.loc[~invalid_qty].copy()

    negative = sales['quantity'] < 0
    log_event(log, 'Separate negative quantities (possible returns)', negative.sum(), negative.sum(),
              'Exclude from gross demand; retain in separate returns CSV for review')
    returns = sales.loc[negative].copy()
    sales = sales.loc[~negative].copy()

    unknown = ~sales['store_id'].isin(stores['store_id'])
    log_event(log, 'Quarantine store IDs missing from lookup', unknown.sum(), unknown.sum(),
              'Prevent unmatched store weather joins')
    unknown_stores = sales.loc[unknown].copy()
    sales = sales.loc[~unknown].copy()

    sales['date'] = sales['timestamp'].dt.normalize()
    sales['sales_amount'] = sales['quantity'] * sales['unit_price']
    # Do not guess SKU aliases; SKU mappings must be reviewed and applied separately.
    log_event(log, 'Finish cleaned positive-demand transactions', len(sales), 0,
              f'{raw_rows:,} raw rows -> {len(sales):,} usable positive-demand rows')
    rejects = {'invalid_prices': price_rejected, 'invalid_quantities': qty_rejected,
               'negative_quantity_returns': returns, 'unknown_stores': unknown_stores}
    return sales.reset_index(drop=True), rejects


def main():
    log = []
    tx_path = RAW / 'walmart_transactions.csv'
    stores_path = RAW / 'store_locations.csv'
    if not tx_path.is_file() or not stores_path.is_file():
        raise FileNotFoundError(f'Expected {tx_path} and {stores_path}. Run in your cloned repository.')
    tx = pd.read_csv(tx_path)
    stores_raw = pd.read_csv(stores_path)
    stores = clean_stores(stores_raw, log)
    sales, rejects = clean_transactions(tx, stores, log)
    OUT.mkdir(parents=True, exist_ok=True)
    stores.to_csv(OUT / 'stores_clean.csv', index=False)
    sales.to_csv(OUT / 'transactions_clean.csv', index=False)
    pd.DataFrame(log).to_csv(OUT / 'cleaning_decision_log.csv', index=False)
    for label, frame in rejects.items():
        frame.to_csv(OUT / f'{label}.csv', index=False)
    print(f'Raw transactions: {len(tx):,}; cleaned positive demand rows: {len(sales):,}')
    print(f'Unique stores: {len(stores)}; date range: {sales.date.min()} to {sales.date.max()}')
    print(pd.DataFrame(log).to_string(index=False))
    print(f'Wrote outputs to {OUT}')

if __name__ == '__main__':
    main()
