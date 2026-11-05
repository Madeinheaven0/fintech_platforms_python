from fintech_cli.engine.domain import OrderEvent, SignalEvent, FillEvent, MarketEvent


class EventQueue:
    """the class that serves as a link between the other classes"""

    def __init__(self):
        self._order_event: OrderEvent | None = None
        self._signal_event: SignalEvent | None = None
        self._fill_event: FillEvent | None = None
        self._market_event: MarketEvent | None = None

    @property
    def order_event(self) -> OrderEvent | None:
        if self._order_event is not None:
            return self._order_event

    @order_event.setter
    def order_event(self, order_event: OrderEvent) -> None:
        self._order_event = order_event

    @property
    def signal_event(self) -> SignalEvent | None:
        if self._signal_event is not None:
            return self._signal_event

    @signal_event.setter
    def signal_event(self, signal_event: SignalEvent) -> None:
        self._signal_event = signal_event

    @property
    def fill_event(self) -> FillEvent | None:
        if self._fill_event is not None:
            return self._fill_event

    @fill_event.setter
    def fill_event(self, fill_event: FillEvent) -> None:
        self._fill_event = fill_event

    @property
    def market_event(self) -> MarketEvent | None:
        if self._market_event is not None:
            return self._market_event

    @market_event.setter
    def market_event(self, market_event: MarketEvent) -> None:
        self._market_event = market_event