from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import typer

from fintech_cli.analytics import AnalyticsData
from fintech_cli.models.arbitrage import ForwardContract, CashAndCarryPricer
from fintech_cli.profiling import profile_performance


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
    pathfile_to_fetch: str = typer.Argument(..., help="Path to the source data file"),
    pathfile_to_save: str = typer.Argument(..., help="Path where the Parquet output will be saved"),
    window: int = typer.Option(14, "--window", "-w", help="Rolling window size"),
    vol_threshold: float = typer.Option(0.02, "--vol-threshold", help="Volatility alert threshold"),
    returns_threshold: float = typer.Option(0.05, "--returns-threshold", help="Returns alert threshold"),
    trading_days: int = typer.Option(252, "--trading-days", help="Number of trading days per year"),
    name: str = typer.Option("default", "--name", "-n", help="Dataset identifier name"),
    profile: bool = typer.Option(False, "--profile", "-p", help="Enable execution time and memory profiling"),
):
    profiled_pipeline = profile_performance(active=profile)(pipeline)

    profiled_pipeline(
        pathfile_to_fetch=pathfile_to_fetch,
        pathfile_to_save=pathfile_to_save,
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

if __name__ == "__main__":
    app()