from datetime import datetime
from decimal import Decimal

import pytest
from fintech_cli.models.arbitrage import ForwardContract, CashAndCarryPricer


def test_forward_contract():
    spot_price = 100.0
    strike_price = 100.0
    free_rate = 0.08
    dividend_rate = 0.05
    val_date = datetime(2020, 1, 1)
    maturity_date = datetime(2020, 2, 1)
    forward_contract = ForwardContract(
        spot_price=spot_price,
        strike_price=strike_price,
        free_rate=free_rate,
        dividend_rate=dividend_rate,
        val_date=val_date,
        maturity_date=maturity_date,
    )

    assert forward_contract.spot_price == spot_price
    assert forward_contract.strike_price == strike_price
    assert forward_contract.free_rate == free_rate
    assert forward_contract.dividend_rate == dividend_rate
    assert forward_contract.val_date == val_date
    assert forward_contract.maturity_date == maturity_date

def test_forward_contract_with_invalid_spot_price():
    spot_price = -100.0
    strike_price = 100.0
    free_rate = 0.08
    dividend_rate = 0.05
    val_date = datetime(2020, 1, 1)
    maturity_date = datetime(2020, 2, 1)

    with pytest.raises(ValueError):
        forward_contract = ForwardContract(
            spot_price=spot_price,
            strike_price=strike_price,
            free_rate=free_rate,
            dividend_rate=dividend_rate,
            val_date=val_date,
            maturity_date=maturity_date,
        )

def test_compute_time_to_maturity(contract):
    time_to_maturity = CashAndCarryPricer.time_to_maturity(contract)

    assert  isinstance(time_to_maturity, Decimal)