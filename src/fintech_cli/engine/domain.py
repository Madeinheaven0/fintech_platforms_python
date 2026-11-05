from datetime import datetime
from collections import deque
import enum
from dataclasses import dataclass
from typing import List, Dict

import polars as pl


class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"

class OrderStatus(enum.Enum):
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"

class Side(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class SignalType(enum.Enum):
    LONG = "LONG"
    SHORT = "SHORT"

@dataclass
class MarketEvent:
        timestamp: datetime
        symbol: str
        open_price: float
        close_price: float
        high_price: float
        low_price: float
        volume: float


@dataclass
class SignalEvent:
    timestamp: datetime
    symbol: str
    price: float
    signal_type: SignalType



@dataclass
class OrderEvent:
    timestamp: datetime
    symbol: str
    order_type: OrderType
    side: Side
    size: float
    price: float
    status: OrderStatus


@dataclass
class FillEvent:
    timestamp: datetime
    symbol: str
    size: float
    side: Side
    fill_price: float
    commission: float


class StrategyBuffer:
    def __init__(self, size: int) -> None:
        self._buffer: deque[MarketEvent]= deque(maxlen=size)

    def append(self, event: MarketEvent) -> None:
        self._buffer.append(event)

    @property
    def buffer(self) -> deque[MarketEvent]:
        return self._buffer

    def _convert_to_polars_format(self):
        buffer_list: List[Dict] = []

        for event in self._buffer:
            market_event = {
                "timestamp": event.timestamp,
                "symbol": event.symbol,
                "open": event.open_price,
                "close": event.close_price,
                "high": event.high_price,
                "low": event.low_price,
                "volume": event.volume,
            }
            buffer_list.append(market_event)
        return buffer_list

    def return_polars(self):
        buffer_list = self._convert_to_polars_format()
        return pl.DataFrame(buffer_list)


    def length(self) -> int:
        return len(self._buffer)


class PendingOrder:
    def __init__(self) -> None:
        self._orders: List[OrderEvent] = []

    def append(self, order: OrderEvent) -> None:
        self._orders.append(order)

    def pop(self, order: OrderEvent) -> None:
        position = self._orders.index(order)
        self._orders.pop(position)

    @property
    def orders(self) -> List[OrderEvent]:
        return self._orders

class ArchiveOrder:
    def __init__(self) -> None:
        self._orders = []

    def append(self, event: OrderEvent) -> None:
        self._orders.append(event)

    @property
    def orders(self) -> List[OrderEvent]:
        return self._orders
