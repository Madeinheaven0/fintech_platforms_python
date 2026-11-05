from datetime import datetime
from random import random, seed
from domain import FillEvent, OrderEvent


class ExecutionHandler:
    def __init__(self, commission: float) -> None:
        self.commission = commission

    def _create_filled_price(self, order: OrderEvent):
        seed(0)
        return order.price + random()

    def _handle(self, order: OrderEvent) -> FillEvent:
        fill_price = self._create_filled_price(order)
        return FillEvent(
            timestamp=datetime.now(),
            symbol=order.symbol,
            size=order.size,
            side=order.side,
            fill_price=fill_price,
            commission=self.commission
        )
