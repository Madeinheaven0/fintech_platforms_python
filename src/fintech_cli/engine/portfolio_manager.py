from typing import Union, Dict, Tuple
from domain import OrderEvent, SignalEvent, Side, ArchiveOrder, PendingOrder


class PortfolioManager:
    def __init__(
            self,
            initial_cash: float,
            n_assets: Union[int,  Dict[str, int]],
            stop_loss: float
    ) -> None:

        self._initial_cash = initial_cash
        self._value = float | None
        self._n_assets = n_assets
        self._stop_loss = stop_loss
        self._pending_orders = PendingOrder()
        self._archive_orders = ArchiveOrder()

    def _compute_portfolio_value(
            self,
            signal: SignalEvent
    ) -> float:
        if isinstance(self._n_assets, int):
            self._value = self._initial_cash + (self._n_assets * signal.price)
        elif isinstance(self._n_assets, dict):
            pass
            # symbol = self._n_assets.get(signal.symbol)

            # if symbol is None:
              #  print("The symbol was not found in the portfolio")
            # if symbol not in self._n_assets.keys():
             #   print(f"The symbol {symbol} was not found in the portfolio: {self._n_assets.keys()}")

    def _compute_order_size(self, signal: SignalEvent) -> float:
        pass

    def save_pending_order(self, order: OrderEvent) -> None:
        self._pending_orders.append(order)

    def save_archive_order(self, order: OrderEvent) -> None:
        self._archive_orders.append(order)



