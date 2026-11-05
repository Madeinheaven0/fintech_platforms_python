from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import typer
import polars as pl
import pandas as pd

from fintech_cli.analytics import AnalyticsData
from fintech_cli.models.arbitrage import ForwardContract, CashAndCarryPricer
from fintech_cli.profiling import profile_performance
import fintech_cli.backtest.vectorized as backtest
from fintech_cli.configuration_errors import ConfigurationError
from fintech_cli.core.vectorized import MonteCarloBlackScholes, MonteCarloHeston


app = typer.Typer()

def pipeline(
    pathfile_to_fetch: str,
    pathfile_to_save: str,
    window: int,
    vol_threshold: float,
    returns_threshold: float,
    trading_days: int,
    name: str,
):
    analytics_data = AnalyticsData(pathfile=pathfile_to_fetch)
    analytics_data.load_data()
    analytics_data.compute_metrics(window=window, trading_days=trading_days)
    analytics_data.compute_alerts(
        vol_threshold=vol_threshold,
        returns_threshold=returns_threshold
    )

    print(analytics_data.asset_data)
    print(analytics_data.metrics)
    print(analytics_data.alerts)
    print(analytics_data.dataset.head(10))

    analytics_data.save_dataset_to_parquet(pathfile=Path(pathfile_to_save), name=name)


@app.command("analytics")
def run_analytics(
    path_file_to_fetch: str = typer.Argument(..., help="Path to the source data file"),
    path_file_to_save: str = typer.Argument(..., help="Path where the Parquet output will be saved"),
    window: int = typer.Option(14, "--window", "-w", help="Rolling window size"),
    vol_threshold: float = typer.Option(0.02, "--vol-threshold", help="Volatility alert threshold"),
    returns_threshold: float = typer.Option(0.05, "--returns-threshold", help="Returns alert threshold"),
    trading_days: int = typer.Option(252, "--trading-days", help="Number of trading days per year"),
    name: str = typer.Option("default", "--name", "-n", help="Dataset identifier name"),
    profile: bool = typer.Option(False, "--profile", "-p", help="Enable execution time and memory profiling"),
):
    profiled_pipeline = profile_performance(active=profile)(pipeline)

    profiled_pipeline(
        pathfile_to_fetch=path_file_to_fetch,
        pathfile_to_save=path_file_to_save,
        window=window,
        vol_threshold=vol_threshold,
        returns_threshold=returns_threshold,
        trading_days=trading_days,
        name=name,
    )

@app.command("arbitrage")
def run_arbitrage(
        spot: float = typer.Option(..., "--spot", "-s", help="Spot price of the underlying asset"),
        strike: float = typer.Option(..., "--strike", "-k", help="Strike Price / Forward"),
        r: float = typer.Option(..., "--rate", "-r", help="Risk-free rate (e.g., 0.05)"),
        div: float = typer.Option(0.0, "--dividend", "-d", help="Dividend rate (e.g., 0.02)"),
        val_date_str: str = typer.Option(..., "--val-date", help="Valuation date (YYYY-MM-DD HH:MM)"),
        mat_date_str: str = typer.Option(..., "--mat-date", help="Maturity date (YYYY-MM-DD HH:MM)"),
):
    """Calculates the theoretical price of a futures contract and detects the basis."""
    try:
        val_dt = datetime.strptime(val_date_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        mat_dt = datetime.strptime(mat_date_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)

        contract = ForwardContract(
            spot_price=spot,
            strike_price=strike,
            free_rate=r,
            dividend_rate=div,
            val_date=val_dt,
            maturity_date=mat_dt
        )

        theo_price = CashAndCarryPricer.calculate_forward_price(contract)
        t_years = CashAndCarryPricer.time_to_maturity(contract)

        typer.echo(f"--- Arbitration Engine Results ---")
        typer.echo(f"Remaining time (T) : {float(t_years):.4f} years")
        typer.echo(f"Theoretical price (F) : {float(theo_price):.4f}")
        typer.echo(f"Entered market price : {strike}")

        basis = Decimal(str(strike)) - theo_price
        typer.echo(f"Spread (Basis) : {float(basis):.4f}")

    except Exception as e:
        typer.echo(f"Runtime error : {e}", err=True)
        raise typer.Exit(code=1)

@app.command("backtest")
def run_backtest(
    financial_data_path: str = typer.Option(..., "--path", "-p", help="Path to fetch data (CSV, Excel, Parquet)"),
    std_threshold: float = typer.Option(0.05, "--std", help="The volatility"),
    std_period: int = typer.Option(20, "--period", help="The period size"),
    window: int = typer.Option(20, "--window", "-w", help="The window size"),
    z_score: float = typer.Option(2.5, "--z-score", "-z", help="The z-score"),
    low_alpha: float = typer.Option(0.5, "--low-alpha", "-l", help="The alpha of the long EMA"),
    high_alpha: float = typer.Option(0.8, "--high-alpha", "-h", help="The alpha of the short EMA"),
    period_per_year: int = typer.Option(252, "--period_per_year", "-P", help="The period of trading day"),
):
    financial_dataset = None

    if financial_data_path.endswith(".csv"):
        financial_dataset = pl.read_csv(financial_data_path)
    elif financial_data_path.endswith(".xlsx") or financial_data_path.endswith(".xls"):
        financial_dataset = pl.read_excel(financial_data_path)
    elif financial_data_path.endswith(".parquet") or financial_data_path.endswith(".pq"):
        financial_dataset = pl.read_parquet(financial_data_path)
    else:
        raise ConfigurationError("Unsupported file format. Use CSV, Excel, or Parquet.")

    analytics_instance = backtest.DataAnalytics(
        financial_data=financial_dataset,
        std_threshold=std_threshold,
        std_period=std_period,
        window=window,
        z_score=z_score,
        low_alpha=low_alpha,
        high_alpha=high_alpha,
    )

    backtest_data = analytics_instance.compute_signals()
    metrics = analytics_instance.get_summary_metrics(
        backtest_data=backtest_data,
        periods_per_year=period_per_year
    )

    typer.echo(backtest_data)
    typer.echo(metrics)

@app.command("black_scholes")
def run_monte_carlo_black_scholes(
        s0: float = typer.Argument(..., help="The initial stock price"),
        r: float = typer.Option(0.05, "-r",  help="The real stock price"),
        std: float = typer.Option(0.05, "--std", help="The volatility"),
        T: float = typer.Option(1., "-T", help="The time period in year"),
        step: int = typer.Option(20, "--step", help="The number of step"),
        paths: int = typer.Option(10_000, "--paths", "-p", help="The number of paths"),
        seed: int = typer.Option(0, "--seed", "-s", help="The random seed"),
    ):

    model = MonteCarloBlackScholes(
        S0=s0,
        r=r,
        vol=std,
        T=T,
        step=step,
        paths=paths,
        seed=seed
    )

    model.compute_price()

    typer.echo(model.price)

@app.command("heston")
def run_monte_carlo_heston(
        s0: float = typer.Argument(..., help="The initial stock price"),
        v0: float = typer.Option(0.0, "-v", help="The volatility"),
        r: float = typer.Option(0.05, "-r", help="The real stock price"),
        T: float = typer.Option(1., "-T", help="The time period in year"),
        kappa: float = typer.Option(0.0, "--kappa", "-k",  help="The kappa"),
        theta: float = typer.Option(0.0, "--theta", "-t", help="The theta"),
        xi: float = typer.Option(0.0, "--xi", "-x", help="The xi"),
        rho: float = typer.Option(0.0, "--rho", help="The rho"),
        step: int = typer.Option(20, "--step", help="The number of step"),
        paths: int = typer.Option(10_000, "--paths", "-p", help="The number of paths"),
        seed: int = typer.Option(0, "--seed", help="The random seed"),
    ):

    model = MonteCarloHeston(
        S0=s0,
        r=r,
        v0=v0,
        rho=rho,
        kappa=kappa,
        theta=theta,
        xi=xi,
        step=step,
        paths=paths,
        seed=seed,
        T=T
    )

    model.compute_price()
    typer.echo(model.price)

    @app.command("full-pipeline")
    def run_full_pipeline(
            path_fetch: str = typer.Argument(..., help="Raw data source file"),
            path_save: str = typer.Argument(..., help="Path to save processed analytics parquet"),
            window_analytics: int = typer.Option(14, "--window-analytics", help="Analytics rolling window"),
            window_backtest: int = typer.Option(20, "--window-backtest", help="Backtest window size"),
            std_threshold: float = typer.Option(0.05, "--std", help="Backtest volatility threshold"),
    ):
        """Exécute l'analyse des données puis lance directement le backtest."""
        typer.echo("🚀 Step 1 : Execute analytics...")

        analytics_data = AnalyticsData(pathfile=path_fetch)
        analytics_data.load_data()
        analytics_data.compute_metrics(window=window_analytics, trading_days=252)
        analytics_data.save_dataset_to_parquet(pathfile=Path(path_save), name="pipeline_dataset")

        typer.echo(f"📁 Data saved at {path_save}")
        typer.echo("📈 Step 2 : Launch the backtest...")

        if path_save.endswith(".parquet"):
            financial_dataset = pl.read_parquet(path_save)
        else:
            financial_dataset = pl.read_csv(path_save)

        analytics_instance = backtest.DataAnalytics(
            financial_data=financial_dataset,
            window=window_backtest,
            std_threshold=std_threshold,
        )

        backtest_data = analytics_instance.compute_signals()
        metrics = analytics_instance.get_summary_metrics(backtest_data=backtest_data, periods_per_year=252)

        typer.echo("✅ Pipeline successfully end !")
        typer.echo(metrics)


if __name__ == "__main__":
    app()