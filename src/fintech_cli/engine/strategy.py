import polars as pl

from fintech_cli.engine.domain import StrategyBuffer, MarketEvent, SignalEvent, SignalType


class Strategy:
    def __init__(
            self,
            std_threshold: float,
            window: int = 20,
            std_period: int = 20,
            z_score: float = 2.5,
            very_low_alpha: float = 0.2,
            low_alpha: float = 0.5,
            high_alpha: float = 0.8,
            buffer_size: int = 100,
                 ) -> None:

        self._std_threshold = std_threshold
        self._window = window
        self._std_period = std_period
        self._z_score = z_score
        self._low_alpha = low_alpha
        self._high_alpha = high_alpha
        self._very_low_alpha = very_low_alpha
        self.buffer: StrategyBuffer = StrategyBuffer(size=buffer_size)
        self.data: pl.DataFrame | None = None
        self.ok = False

    def accumulate_event(self, event: MarketEvent) -> None:
        """Strategy class can't calculate indicators if there are not enough of data"""
        self.buffer.append(event)
        if self.buffer.length() > self._window:
            self.ok = True

    def _compute_ema(self, events: pl.DataFrame) -> pl.DataFrame | None:
        return events.with_columns(
            pl.col('close').ewm_mean(alpha=self._low_alpha).alias("long_ema"),
            pl.col('close').ewm_mean(alpha=self._high_alpha).alias("short_ema"),
            pl.col('close').ewm_mean(alpha=self._very_low_alpha).alias("very_long_ema"),
        )

    def _compute_rsi(self, events: pl.DataFrame) -> pl.DataFrame:
        delta = events["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm_mean(alpha=1 / self._window)
        avg_loss = loss.ewm_mean(alpha=1 / self._window)

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return events.with_columns(rsi.alias("rsi"))

    def _compute_z_score(self, event: pl.DataFrame) -> pl.DataFrame | None:
        return event.with_columns(
            ((pl.col('close') - pl.col('close').rolling_mean(window_size=self._window)) / pl.col('close').rolling_std(window_size=self._window)).alias('z_score')
        )

    def _return_data(self, event: pl.DataFrame) -> pl.DataFrame | None:
        return  event.select(pl.col(['close', 'long_ema', 'short_ema', 'very_long_ema', 'rsi', 'z_score']))

    def _compute_indicator(self, event: pl.DataFrame) -> pl.DataFrame | None:

        event_data = self._compute_ema(event)
        event_data = self._compute_rsi(event_data)
        event_data = self._compute_z_score(event_data)
        return self._return_data(event_data)

    def _compute_signal(self, event: MarketEvent) -> SignalEvent | None:
        self.accumulate_event(event)

        if not self.ok:
            return None

        event_data = self.buffer.return_polars()
        if event_data.empty:
            pass

        data = self._compute_signal(event_data)

        signal_event = data.select(
            (pl.when(
                (pl.col('close') > pl.col('very_long_ema'))
                &  (pl.col('short_ema') > pl.col('long_ema'))
                & (pl.col('rsi') > 50.)
                & (pl.col('rsi') < 70.)
            ).
            then(1)
            .when(
                (pl.col('long_ema') > pl.col('short_ema'))
                & (pl.col('rsi') > 75.)
            ).then(-1)
            .otherwise(0)).last()
        ).item()

        if signal_event == 1:
            return SignalEvent(
            timestamp=event.timestamp,
            symbol=event.symbol,
            price=event.close_price,
            signal_type=SignalType.LONG,
        )
        elif signal_event == -1:
            return SignalEvent(
                timestamp=event.timestamp,
                symbol=event.symbol,
                price=event.close_price,
                signal_type=SignalType.SHORT,
            )
        else:
            return None





