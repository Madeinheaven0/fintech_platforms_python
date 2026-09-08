from pathlib import Path

import typer
from numba.np.arraymath import np_trim_zeros

from src.parser.analytics import AnalyticsData

app = typer.Typer()

@app.command()
def main(
        pathfile_to_fetch: str,
        pathfile_to_save: str,
        window: int,
        vol_threshold: int,
        returns_threshold: int,
        trading_days: int,
        name: str
    ):
    analytics_data = AnalyticsData(pathfile=pathfile_to_fetch)
    analytics_data.load_data()
    analytics_data.compute_metrics(window=window, trading_days=trading_days)
    analytics_data.compute_alerts(
        vol_threshold=vol_threshold,
        returns_threshold=returns_threshold
    )

    assert_data = analytics_data.asset_data
    result_metics = analytics_data.metrics
    result_alerts = analytics_data.alerts

    print(assert_data)
    print(result_metics)
    print(result_alerts)
    print(analytics_data.dataset.head(10))

    analytics_data.save_dataset_to_parquet(pathfile= Path(pathfile_to_save), name= name)



