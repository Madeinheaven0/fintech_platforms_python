from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal

class ForwardContract(BaseModel):
    spot_price: float = Field(gt=0)
    strike_price: float = Field(gt=0)
    free_rate: float
    dividend_rate: float
    val_date: datetime
    maturity_date: datetime


class CashAndCarryPricer:
    @staticmethod
    def time_to_maturity(contract: ForwardContract) -> Decimal:
        delta = contract.maturity_date - contract.val_date
        delta = Decimal(str(delta.total_seconds()))
        numerator = Decimal((3600.0 * 24.0 * 365.0))
        return delta / numerator

    @staticmethod
    def calculate_forward_price(cls, contract: ForwardContract) -> Decimal:
        t = cls.time_to_maturity(contract)
        rate_diff = Decimal(str(contract.free_rate - contract.dividend_rate))
        exponent = rate_diff * t
        discount_factor = exponent.exp()
        return Decimal(contract.spot_price * discount_factor)

    @classmethod
    def detect_arbitrage(cls, contract: ForwardContract, market_future_price: Decimal,
                         threshold: Decimal = Decimal("0.05")) -> str:
        """
        Detects arbitrage opportunities by comparing the theoretical price to the market price.
        """
        theo_price = cls.calculate_forward_price(contract)
        basis = market_future_price - theo_price

        if basis > threshold:
            return f"Cash-and-carry opportunity: Overvalued futures contract (Basis: {basis:.4f}). Sell the futures contract, buy the spot asset."
        elif basis < -threshold:
            return f"REVERSE CASH & CARRY Opportunity: Undervalued future (Basis: {basis:.4f}). Buy the future, sell the spot."
        else:
            return f"Balanced market (Basis: {basis:.4f}). No profitable arbitrage."
