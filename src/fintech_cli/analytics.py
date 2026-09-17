import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import polars as pl

from data.market_data import MarketDataParser


class AnalyticsData:
    """
    Analytics class to compute basic market metrics and alert users
    when volatility or return thresholds are breached.
    """

    def __init__(self, pathfile: str) -> None:
        self.market_data = MarketDataParser()
        self.pathfile = pathfile
        self._asset_data: Dict[str, List[Dict[str, Union[str, float]]]] = {}
        self._dataset: Optional[pl.DataFrame] = None
        self._metrics: Dict[str, Dict[str, float | List[float]]] = {}
        self._alerts: Dict[str, Dict[str, str]] = {}
        self._window: int = 0

    def load_data(self) -> None:
        """Loads market data and flattens it into a single Polars DataFrame."""
        self._asset_data = self.market_data.load_path(self.pathfile)

        # Flatten the asset dictionary into a single list of dict records
        all_records = [
            record
            for records in self._asset_data.values()
            for record in records
        ]

        if all_records:
            self._dataset = pl.DataFrame(all_records)
        else:
            self._dataset = pl.DataFrame()

    def _compute_returns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Compute the daily log returns."""
        asset_col = "symbol" if "symbol" in df.columns else "ticker"

        return df.with_columns(
            (pl.col("Close") / pl.col("Close").shift(1).over(asset_col))
            .log()
            .fill_null(0.0)
            .alias("log_returns")
        )

    def _compute_rolling_means(self, window: int, df: pl.DataFrame) -> pl.DataFrame:
        """Compute the rolling mean on closing prices."""
        return df.with_columns(
            pl.col("Close")
            .rolling_mean(window)
            .alias(f"rolling_mean_{window}")
        )

    def _compute_annualized_volatility(
            self, window: int, trading_days: int, df: pl.DataFrame
    ) -> pl.DataFrame:
        """Compute rolling annualized volatility using standard deviation of log returns."""
        if "log_returns" not in df.columns:
            df = self._compute_returns(df=df)

        return df.with_columns(
            (pl.col("log_returns").rolling_std(window) * (trading_days ** 0.5))
            .alias(f"annualized_volatility_{window}")
        )

    def compute_metrics(self, window: int = 20, trading_days: int = 252) -> None:
        self._window = window

        if not self._asset_data:
            self.load_data()

        processed_dfs = []
        for asset, data in self._asset_data.items():
            if not data:
                continue

            df = pl.DataFrame(data)

            if "ticker" not in df.columns:
                df = df.with_columns(pl.lit(asset).alias("ticker"))

            if "date" in df.columns:
                df = df.sort("Date")

            df = self._compute_returns(df=df)
            df = self._compute_rolling_means(window=window, df=df)
            df = self._compute_annualized_volatility(
                window=window, df=df, trading_days=trading_days
            )
            processed_dfs.append(df)

            vol_col = f"annualized_volatility_{window}"
            last_vol = df[vol_col].drop_nulls().tail(1)

            self._metrics[asset] = {
                "returns": df["log_returns"].to_list(),
                "total_returns": float(df["log_returns"].sum()),
                "rolling_means": df[f"rolling_mean_{window}"].to_list(),
                "annualized_volatility": df[vol_col].to_list(),
                "last_volatility": float(last_vol[0]) if len(last_vol) > 0 else 0.0,
            }

        if processed_dfs:
            self._dataset = pl.concat(processed_dfs)

    def compute_alerts(self, vol_threshold: float, returns_threshold: float) -> None:
        if not self._metrics:
            self.compute_metrics()

        for asset in self._asset_data.keys():
            self._alerts[asset] = {}
            if self._metrics[asset]["total_returns"] < returns_threshold:
                self._alerts[asset]["total_returns"] = "The total return is too low"
            if self._metrics[asset]["last_volatility"] > vol_threshold:
                self._alerts[asset][f"annualized_volatility_{self._window}"] = "The annualized volatility is too high"

    def save_dataset_to_parquet(self, pathfile: Path, name: str) -> None:
        target_dir = pathfile if pathfile.is_dir() else pathfile.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        path = target_dir / f"{name}.parquet"
        if self._dataset is not None:
            self._dataset.write_parquet(path)

    @property
    def metrics(self) -> Dict[str, Dict[str, float | List[float]]]:
        return self._metrics

    @property
    def alerts(self) -> Dict[str, Dict[str, str]]:
        return self._alerts

    @property
    def asset_data(self) -> Dict[str, List[Dict[str, Union[str, float]]]]:
        if not self._asset_data:
            self.load_data()
        return self._asset_data

    @property
    def dataset(self) -> pl.DataFrame | None:
        if self._dataset is None:
            self.compute_metrics()
        return self._dataset