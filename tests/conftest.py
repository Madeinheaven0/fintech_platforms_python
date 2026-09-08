import pytest

from pathlib import Path

from data.market_data import MarketDataParser



@pytest.fixture
def parser():
    return MarketDataParser()


@pytest.fixture
def data_path():
    return Path(__file__).parent / "test_data"

print( Path(__file__).parent / "test_data")

@pytest.fixture
def multi_asset_data():
    return {
        'Date': '2026-03-01',
        'Open': 180.25,
        'High': 182.5,
        'Low': 179.80,
        'Close': 181.90,
        'Volume': 52000000
    }