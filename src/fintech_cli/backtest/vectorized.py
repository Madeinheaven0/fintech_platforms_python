import pandas as pd
from typing import List, Tuple
from pandas.errors import EmptyDataError
import polars as pl
import polars.selectors as cs


class DataAnalytics:
    def __init__(
            self,
            financial_data: pd.DataFrame | pl.DataFrame,
            std_threshold: float,
            window: int = 20,
            std_period: int = 20,
            z_score: float = 2.5,
            low_alpha: float = 0.5,
            high_alpha: float = 0.8,
    ) -> None:
        self._post_init(financial_data, std_threshold, window, std_period, z_score, low_alpha,
                        high_alpha)

        self.financial_data = self._convert_data(financial_data)
        self.assets_columns = [col for col in self.financial_data.columns if col != "Date"]

        self.std_threshold: float = std_threshold
        self.window: int = window
        self.std_period: int = std_period
        self.z_score_threshold: float = z_score

        self._pair_asset: List[Tuple[str, str]] = []

        self._analyzed_data: pl.DataFrame = self.financial_data.clone()
        self._analyzed_data_pair: pl.DataFrame = pl.select(
            pl.col("Date")) if "Date" in self.financial_data.columns else pl.DataFrame()

    def _post_init(
            self,
            financial_data: pd.DataFrame,
            std_threshold: float,
            window: int,
            std_period: int,
            z_score: float,
            low_alpha: float,
            high_alpha: float,
    ) -> None:
        if financial_data.empty:
            raise EmptyDataError("The financial data is empty")
        if std_threshold < 0:
            raise ValueError('The volatility cannot be negative')
        if std_period <= 0:
            raise ValueError('The volatility period  cannot be negative')
        if z_score <= 0:
            raise ValueError('The z-score cannot be negative')
        if window <= 0:
            raise ValueError('The window period cannot be negative')
        if low_alpha < 0 or high_alpha < 0:
            raise ValueError('The low and high alpha cannot be negative')
        if z_score <= 0:
            raise ValueError('The z-score cannot be negative')
        if not isinstance(financial_data, pl.DataFrame):
            raise TypeError("The financial data is not a DataFrame")
        if not isinstance(std_threshold, float):
            raise TypeError("The std_threshold is not a float")
        if not isinstance(window, int):
            raise TypeError("The window period is not a int")
        if not isinstance(std_period, int):
            raise TypeError("The std_period is not a int")
        if not isinstance(z_score, float):
            raise TypeError("The z_score is not a float")
        if not isinstance(low_alpha, float):
            raise TypeError("The low_alpha is not a float")
        if not isinstance(high_alpha, float):
            raise TypeError("The high_alpha is not a float")

    def _convert_data(self, data) -> pl.DataFrame:
        if isinstance(data, pd.DataFrame):
            return pl.from_pandas(data)
        if isinstance(data, pl.DataFrame):
            return data
        raise TypeError("The data format is not supported")

    def _select_assets_corr(self, threshold: float = 0.8):
        # Computation of the correlation matrix on the numeric columns
        num_cols = [c for c in self.assets_columns if c != "Date"]
        corr_matrix = self.financial_data.select(num_cols).corr()
        cols = corr_matrix.columns

        for col_idx in range(len(cols)):
            for i in range(col_idx + 1, len(cols)):
                asset_a, asset_b = cols[col_idx], cols[i]
                corr_val = corr_matrix.select(pl.corr(asset_a, asset_b)).item()
                if corr_val is not None and corr_val > threshold:
                    self._pair_asset.append((asset_a, asset_b))

    def _compute_rolling_spread(self):
        for pair in self._pair_asset:
            asset_a, asset_b = pair[0], pair[1]
            # Computation of the spread propre (ex: Prix A - beta * Prix B)
            pair_df = self.financial_data.select([
                "Date",
                (
                        pl.col(asset_a) - pl.col(asset_b) *
                        (pl.rolling_cov(pl.col(asset_a), pl.col(asset_b), window_size=self.window) /
                         pl.col(asset_b).rolling_var(window_size=self.window))
                ).alias(f"{asset_a}-{asset_b}_spread")
            ])

            if self._analyzed_data_pair.width == 0:
                self._analyzed_data_pair = pair_df
            else:
                self._analyzed_data_pair = self._analyzed_data_pair.join(pair_df, on="Date", how="outer")

    def _compute_ema(self):
        num_cols = [c for c in self.assets_columns if c != "Date"]
        ema = self.financial_data.with_columns(
            pl.col(num_cols).ewm_mean(alpha=self.low_alpha).name.suffix("_long_ema"),
            pl.col(num_cols).ewm_mean(alpha=self.high_alpha).name.suffix("_short_ema")
        ).select(
            ["Date"] + [c for c in cs.ends_with("_long_ema").expanded_columns] + [c for c in cs.ends_with(
                "_short_ema").expanded_columns]
        )

        self._analyzed_data = self._analyzed_data.join(ema, on="Date", how="left")

    def _compute_z_score(self):
        # Moving Z-score mobile on the pair
        spread_cols = [c for c in self._analyzed_data_pair.columns if "spread" in c]
        if spread_cols:
            self._analyzed_data_pair = self._analyzed_data_pair.with_columns([
                ((pl.col(c) - pl.col(c).rolling_mean(window_size=self.window)) /
                 pl.col(c).rolling_std(window_size=self.window)).alias(f"{c}_z_score")
                for c in spread_cols
            ])

        # Z-score solo for assets
        num_cols = [c for c in self.assets_columns if c != "Date"]
        self._analyzed_data = self._analyzed_data.with_columns([
            ((pl.col(col) - pl.col(f"{col}_long_ema")) / pl.col(col).rolling_std(window_size=self.std_period)).alias(
                f"{col}_long_ema_z_score")
            for col in num_cols
        ])

    def compute_signals(self):
        self._select_assets_corr()
        self._compute_rolling_spread()
        self._compute_ema()
        self._compute_z_score()

        backtest_data = self._analyzed_data.join(self._analyzed_data_pair, how="inner", on="Date")

        # 1. Solo signal per asset
        for asset in [c for c in self.assets_columns if c != "Date"]:
            backtest_data = backtest_data.with_columns(
                pl.when(
                    (pl.col(f"{asset}_short_ema") > pl.col(f"{asset}_long_ema")) &
                    (pl.col(f"{asset}_long_ema_z_score") > self.z_score_threshold)
                ).then(-1)
                .when(
                    (pl.col(f"{asset}_short_ema") < pl.col(f"{asset}_long_ema")) &
                    (pl.col(f"{asset}_long_ema_z_score") < -self.z_score_threshold)
                ).then(1)
                .otherwise(0)
                .alias(f"{asset}_signal")
            )

        # 2. Pair signals
        for pair in self._pair_asset:
            pair_asset = f'{pair[0]}-{pair[1]}'
            z_col = f"{pair_asset}_spread_z_score"

            if z_col in backtest_data.columns:
                backtest_data = backtest_data.with_columns(
                    pl.when(
                        (pl.col(z_col) > self.z_score_threshold) &
                        (pl.col(f"{pair[0]}_long_ema_z_score") > self.z_score_threshold)
                    ).then(1)
                    .when(
                        (pl.col(z_col) < -self.z_score_threshold) &
                        (pl.col(f"{pair[1]}_long_ema_z_score") < -self.z_score_threshold)
                    ).then(1)
                    .otherwise(0)
                    .alias(f"{pair_asset}_signal")
                )

        return backtest_data

    def compute_pnl(self, backtest_data: pl.DataFrame) -> pl.DataFrame:
        """
        Compute the returns and the PnL for each signal (Solo and Pairs)
        """
        exprs = []

        num_cols = [c for c in self.assets_columns if c != "Date"]
        for asset in num_cols:
            signal_col = f"{asset}_signal"
            if signal_col in backtest_data.columns:
                exprs.extend([
                    # Return of the asset between t-1 and t
                    pl.col(asset).pct_change().alias(f"{asset}_returns"),

                    # PnL of the strategy solo (Shifted Signal * Return)
                    (pl.col(signal_col).shift(1) * pl.col(asset).pct_change()).alias(f"{asset}_pnl")
                ])

        # 2. PnL of the Pairs (Spread Returns)
        for pair in self._pair_asset:
            pair_asset = f'{pair[0]}-{pair[1]}'
            signal_col = f"{pair_asset}_signal"
            spread_col = f"{pair_asset}_spread"

            if signal_col in backtest_data.columns and spread_col in backtest_data.columns:
                exprs.extend([
                    pl.col(spread_col).pct_change().alias(f"{pair_asset}_spread_returns"),
                    (pl.col(signal_col).shift(1) * pl.col(spread_col).pct_change()).alias(f"{pair_asset}_pnl")
                ])

        # Application of the expressions
        backtest_data = backtest_data.with_columns(exprs)

        pnl_cols = [c for c in backtest_data.columns if c.endswith("_pnl")]
        if pnl_cols:
            backtest_data = backtest_data.with_columns([
                (1 + pl.col(col).fill_null(0)).cum_prod().alias(f"{col}_equity_curve")
                for col in pnl_cols
            ])

        return backtest_data

    def compute_performance_metrics(self, backtest_data: pl.DataFrame, periods_per_year: int = 252) -> pl.DataFrame:
        """
        Compute the global sharpe, the Max Drawdown and the Rolling Sharpe for each PnL.
        """
        pnl_cols = [c for c in backtest_data.columns if c.endswith("_pnl")]

        metrics_expressions = []

        for col in pnl_cols:
            base_name = col.replace("_pnl", "")
            equity_col = f"{col}_equity_curve"

            if equity_col not in backtest_data.columns:
                continue

            # 1. Compute the Max Drawdown (MDD)
            # Formula : (Equity - Rolling Peak) / Rolling Peak
            mdd_expr = (
                    (pl.col(equity_col) - pl.col(equity_col).cum_max())
                    / pl.col(equity_col).cum_max()
            ).min().alias(f"{base_name}_max_drawdown")

            # 2. Sharpe Ratio Global Annualized
            # Sharpe = (Mean / Std) * sqrt(periods_per_year)
            sharpe_expr = (
                    (pl.col(col).mean() / pl.col(col).std()) * (periods_per_year ** 0.5)
            ).alias(f"{base_name}_sharpe_ratio")

            metrics_expressions.extend([mdd_expr, sharpe_expr])

            # 3. Rolling Sharpe Ratio
            rolling_window = 60
            rolling_sharpe = (
                    (pl.col(col).rolling_mean(window_size=rolling_window) /
                     pl.col(col).rolling_std(window_size=rolling_window)) * (periods_per_year ** 0.5)
            ).alias(f"{base_name}_rolling_sharpe_{rolling_window}")

            backtest_data = backtest_data.with_columns(rolling_sharpe)

        return backtest_data

    def get_summary_metrics(self, backtest_data: pl.DataFrame, periods_per_year: int = 252) -> pl.DataFrame:
        pnl_cols = [c for c in backtest_data.columns if c.endswith("_pnl")]
        summary_exprs = []

        for col in pnl_cols:
            base_name = col.replace("_pnl", "")
            equity_col = f"{col}_equity_curve"

            if equity_col in backtest_data.columns:
                summary_exprs.extend([
                    # Sharpe Global
                    ((pl.col(col).mean() / pl.col(col).std()) * (periods_per_year ** 0.5)).alias(f"{base_name}_Sharpe"),
                    # Max Drawdown Global
                    (((pl.col(equity_col) - pl.col(equity_col).cum_max()) / pl.col(equity_col).cum_max()).min()).alias(
                        f"{base_name}_MaxDD")
                ])

        return backtest_data.select(summary_exprs)