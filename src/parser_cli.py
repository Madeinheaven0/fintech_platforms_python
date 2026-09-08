import tracemalloc
from time import perf_counter
from pathlib import Path

import typer

from analytics import AnalyticsData
from src.profiling import profile_performance


app = typer.Typer()

def run_pipeline(
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


@app.command()
def main(
        pathfile_to_fetch: str,
        pathfile_to_save: str,
        window: int,
        vol_threshold: float,
        returns_threshold: float,
        trading_days: int,
        name: str,
        profile: bool = typer.Option(False, "-p", "--profile", help="Enable time and memory profiling"),
        ):
    profiled_pipeline = profile_performance(active=profile)(run_pipeline)

    profiled_pipeline(
        pathfile_to_fetch=pathfile_to_fetch,
        pathfile_to_save=pathfile_to_save,
        window=window,
        vol_threshold=vol_threshold,
        returns_threshold=returns_threshold,
        trading_days=trading_days,
        name=name,
    )

if __name__ == "__main__":
    app()


