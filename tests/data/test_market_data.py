import pytest

from pathlib import Path

from data import MarketDataParser

def test_parse_csv_mono_asset(parser, data_path, multi_asset_data):
    path = str(data_path / "market_data_multi_assets.csv")
    parser.parse_csv_file(pathfile=path)

    assert parser.data["AAPL"][0] ==  multi_asset_data



