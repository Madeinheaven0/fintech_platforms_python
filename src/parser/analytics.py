import polars as pl
from typing import Dict, Union, List, Optional
from pathlib import Path
import os

from data.market_data import MarketDataParser


class AnalyticsData:
    """
        Analytics class who compute basics informations and inform the user
        if threshold are passed
    """
    def __init__(self, pathfile: str) -> None:
        """
        Analytics data class constructor
        :param pathfile: the path of the raw data file (json or csv)
        """
        self.market_data = MarketDataParser()
        self.pathfile = pathfile
        self._asset_data = {}
        self._dataset: Optional[pl.DataFrame] = None
        self._metrics: Dict[str, Dict[str, float | List[float]]] = {}
        self._alerts: Dict[str, Dict[str, str]] = {}
        self._window: int = 0

    def load_data(self) -> None:
        self._asset_data = self.market_data.load_path(self.pathfile)
        self._dataset = pl.DataFrame(self._asset_data)

    def _compute_returns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Compute the daily log returns"""
        return df.with_columns(
            (pl.col("close") / pl.col("close").shift(1))
            .log()
            .fill_null(0.0)
            .alias("log_return")
        )

    def _compute_rolling_means(self, window: int, df: pl.DataFrame) -> pl.DataFrame:
        """Compute the rolling meean"""
        return df.with_columns(
            pl.col("close")
            .rolling_mean(window)
            .alias(f"rolling_mean_{window}")
        )

    def _compute_annalized_volatility(self, window: int, trading_days: int, df: pl.DataFrame) -> pl.DataFrame:
        """Compute the annalized volatility"""
        if 'log_returns' in self._dataset.columns:
            self._compute_returns(df=df)
        return df.with_columns(
            (
            pl.col("log_returns")
             .rolling(window) * (trading_days ** 0.5))
            .alias(f"annualized_volatility_{window}")
        )

    def compute_metrics(self, window: int = 20, trading_days: int = 252) -> None:
        self._window = window

        if not self._asset_data:
            self.load_data()

        processed_df = []
        for asset, data in self._asset_data.items():
            if not data:
                continue

            df = pl.DataFrame(data)

            if "ticker" not in df.columns:
                df = df.with_columns(pl.lit(asset).alias("ticker"))

            if "date" in df.columns:
                df = df.sort("date")

            df = self._compute_returns(df=df)
            df = self._compute_rolling_means(window=window, df=df)
            df = self._compute_annalized_volatility(window=window, df=df, trading_days=trading_days)
            processed_df.append(df)

            vol_col = f"annualized_volatility_{window}"
            last_vol = df[vol_col].drop_nulls().tail(1)

            self._metrics[asset] = {
                "returns": df["log_return"].to_list(),
                "total_returns": float(df["log_return"].sum()),
                "rolling_means": df[f"rolling_mean_{window}"].to_list(),
                "annualized_volatility": df[vol_col].to_list(),
                "last_volatility": float(last_vol[0]) if len(last_vol) > 0 else 0.0,
            }
        if processed_df:
            self._dataset = pl.concat(processed_df)

    def compute_alerts(self, vol_threshold: float, returns_threshold: float) -> None:
        if not self._metrics:
            self.compute_metrics()

        for asset in self._asset_data.keys():
            self._alerts[asset] = {}
            if self._metrics[asset]["total_returns"] < returns_threshold:
                self._alerts[asset]["total_returns"] = "The total returns is too low"
            if self._metrics[asset][f"annualized_volatility_{self._window}"] < vol_threshold:
                self._alerts[asset][f"annualized_volatility_{self._window}"] = "The annualized volatility is too high"

    def save_dataset_to_parquet(self, pathfile: Path, name: str):
        if pathfile.exists():
            path = pathfile / f"{name}.parquet"
            self._dataset.write_parquet(path)
        else:
            os.makedirs(pathfile)
            path = pathfile / f"{name}.parquet"
            self._dataset.write_parquet(path)

    @property
    def metrics(self) ->  Dict[str, Dict[str, float | List[float]]]:
        return self._metrics

    @property
    def alerts(self) -> Dict[str, Dict[str, str]]:
        return self._alerts

    @property
    def asset_data(self) -> Dict[str, Dict[str, Dict[str, Union[str, float]]]] | str:
        if not self.asset_data:
            self.load_data()
        return self._asset_data

    @property
    def dataset(self) -> pl.DataFrame | None:
        if self._dataset is None:
            self.compute_metrics()
        return self._dataset




