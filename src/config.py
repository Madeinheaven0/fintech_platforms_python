from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
DATASET_DIR = ROOT_DIR / "datasets"
GLOBAL_MACRO_DIR = DATASET_DIR / "global_financial_macro"
bitcoin_path = GLOBAL_MACRO_DIR / "bitcoin.csv"
copper_path = GLOBAL_MACRO_DIR / "copper.csv"
gold_path = GLOBAL_MACRO_DIR / "gold.csv"
nasdaq_path = GLOBAL_MACRO_DIR / "nasdaq.csv"
natural_gaz_path = GLOBAL_MACRO_DIR / "natural_gaz.csv"
oil_brent_path = GLOBAL_MACRO_DIR / "oil_brent.csv"
oil_wti_path = GLOBAL_MACRO_DIR / "oil_wti.csv"
silver_path = GLOBAL_MACRO_DIR / "silver.csv"
sp500_path = GLOBAL_MACRO_DIR / "sp500.csv"
us10y_path = GLOBAL_MACRO_DIR / "us10y.csv"
usd_idr_path = GLOBAL_MACRO_DIR / "usd_idr.csv"
usd_index = GLOBAL_MACRO_DIR / "usd_index.csv"
vix_path = GLOBAL_MACRO_DIR / "vix.csv"