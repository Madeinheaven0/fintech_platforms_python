from datetime import datetime

import pytest

from pathlib import Path
from data.market_data import MarketDataParser
from fintech_cli.models.arbitrage import ForwardContract


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


@pytest.fixture
def contract():
    spot_price = 100.0
    strike_price = 100.0
    free_rate = 0.08
    dividend_rate = 0.05
    val_date = datetime(2020, 1, 1)
    maturity_date = datetime(2020, 2, 1)
    return ForwardContract(
        spot_price=spot_price,
        strike_price=strike_price,
        free_rate=free_rate,
        dividend_rate=dividend_rate,
        val_date=val_date,
        maturity_date=maturity_date,
    )