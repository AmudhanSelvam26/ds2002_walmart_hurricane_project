"""Build a reviewable product/SKU mapping and join it to cleaned transactions.
Run from repo root: python src/build_sku_mapping.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
OUT = DATA / 'processed'

FAMILIES = {
    'Pop-Tarts Strawberry': ['PT-12', 'SKU#459812', 'POPTART-STRAW', 'PT_STRAWBERRY'],
    'Bottled Water 24-Pack': ['WTR-24', 'WATER24PK', 'WTR_24PK'],
    'AA Batteries': ['BATT-100', 'BAT-AA4', 'BATT_AA_4PK'],
    'LED Flashlight': ['FLASH-01', 'LED-FLASH'],
    'Light Beer 24-Pack': ['BEER-24', 'LTBEER24'],
    'Monopoly Board Game': ['BG-MONO', 'MONOPOLY-01', 'GAME-MONO'],
    'Playing Cards': ['CARDS-01', 'PLAYCARD-STD'],
    'Streaming Device': ['STREAM-01', 'ROKU-STD'],
    'Canned Soup': ['SOUP-CAN', 'CNSOUP-01'],
    'White Bread': ['BREAD-WH', 'WHITEBREAD'],
    'Peanut Butter': ['PB-16', 'PNUTBTR-16'],
    'Emergency Candles': ['CNDL-EM', 'CANDLE-EMRG'],
    'First Aid Kit': ['FAID-01', 'FIRSTAID-KIT'],
    'Portable Charger': ['CHRG-PORT', 'PORTCHARGER'],
    'Chips Variety Pack': ['CHIPS-VP', 'CHIPVARIETY'],
    'Paper Towels': ['PTOWEL-6', 'PAPERTOWEL6'],
    'Toilet Paper': ['TP-12', 'TOILETPAPER12'],
    'Baby Diapers Size 3': ['DIAP-S3', 'DIAPERS-3'],
    'Baby Formula': ['BFORM-01', 'BABYFORMULA'],
    'Heavy Duty Tarp': ['TARP-HD', 'HDTARP-01'],
}
CATEGORIES = {
    'Pop-Tarts Strawberry': 'Breakfast',
    'Bottled Water 24-Pack': 'Emergency Supplies',
    'AA Batteries': 'Emergency Supplies',
    'LED Flashlight': 'Emergency Supplies',
    'Light Beer 24-Pack': 'Alcohol',
    'Monopoly Board Game': 'Entertainment',
    'Playing Cards': 'Entertainment',
    'Streaming Device': 'Electronics',
    'Canned Soup': 'Grocery',
    'White Bread': 'Grocery',
    'Peanut Butter': 'Grocery',
    'Emergency Candles': 'Emergency Supplies',
    'First Aid Kit': 'Health',
    'Portable Charger': 'Electronics',
    'Chips Variety Pack': 'Snacks',
    'Paper Towels': 'Household',
    'Toilet Paper': 'Household',
    'Baby Diapers Size 3': 'Baby',
    'Baby Formula': 'Baby',
    'Heavy Duty Tarp': 'Emergency Supplies',
}

def build_mapping(catalog):
    rows = [dict(sku=sku, canonical_product=family, canonical_category=CATEGORIES[family])
            for family, skus in FAMILIES.items() for sku in skus]
    mapping = pd.DataFrame(rows)
    mapping['sku'] = mapping['sku'].astype('string').str.strip().str.upper()
    if mapping['sku'].duplicated().any():
        raise ValueError('Same SKU mapped to more than one product')
    all_catalog_skus = set(catalog['sku'].dropna())
    unknown_in_mapping = set(mapping['sku']) - all_catalog_skus
    if unknown_in_mapping:
        raise ValueError(f'Mapped SKUs absent from catalog: {sorted(unknown_in_mapping)}')
    remaining = catalog.loc[~catalog['sku'].isin(mapping['sku']), ['sku','product_name','category']]
    if len(remaining):
        raise ValueError(f'Catalog needs review; unmapped:\n{remaining.to_string(index=False)}')
    return mapping

def main():
    catalog = pd.read_csv(DATA / 'product_catalog.csv')
    catalog['sku'] = catalog['sku'].astype('string').str.strip().str.upper()
    mapping = build_mapping(catalog)
    OUT.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(ROOT / 'src' / 'sku_mapping.csv', index=False)

    sales = pd.read_csv(OUT / 'transactions_clean.csv')
    if 'sku' not in sales.columns:
        raise ValueError(f'Expected SKU column named sku; found {list(sales.columns)}')
    sales['sku'] = sales['sku'].astype('string').str.strip().str.upper()
    before_count = len(sales)
    before_quantity = sales['quantity'].sum()
    enriched = sales.merge(mapping, on='sku', how='left', validate='many_to_one', indicator=True)
    assert len(enriched) == before_count
    assert enriched['quantity'].sum() == before_quantity
    unmapped = enriched.loc[enriched['_merge'] == 'left_only', ['sku']].drop_duplicates()
    unmapped.to_csv(OUT / 'unmapped_skus.csv', index=False)
    if len(unmapped):
        print('WARNING: transactions include unmapped SKUs, review data/processed/unmapped_skus.csv')
    enriched = enriched.drop(columns='_merge')
    enriched.to_csv(OUT / 'transactions_enriched.csv', index=False)
    print('Raw SKU count:', sales['sku'].nunique())
    print('Mapped canonical product count:', enriched['canonical_product'].nunique())
    print('Unmapped SKU count:', len(unmapped))
    print('Rows preserved:', len(enriched), 'Units preserved:', before_quantity)
    print('Wrote', OUT / 'transactions_enriched.csv')

if __name__ == '__main__':
    main()
