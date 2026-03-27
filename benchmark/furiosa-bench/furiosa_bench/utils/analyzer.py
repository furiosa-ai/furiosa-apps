import numpy as np
import pandas as pd


def get_benchmark_power_summary(
    csv_file_path: str, start_dt: str | None, end_dt: str | None, target_csv_file_path: str | None
) -> dict[str, float]:
    """
    Analyzes power consumption data from a CSV file and computes summary statistics.
    Args:
        csv_file_path (str): Path to the CSV file containing power consumption data.
        start_dt (str | None): Start datetime string in ISO format to filter data.
        end_dt (str | None): End datetime string in ISO format to filter data.
        target_csv_file_path (str | None): If provided, filtered data will be saved to this path.
    Returns:
        dict[str, float]: A dictionary containing mean, 95th percentile, and 99th percentile of power consumption.
    """
    df = pd.read_csv(csv_file_path, parse_dates=["timestamp"])

    mask = pd.Series(True, index=df.index)
    if start_dt is not None:
        mask &= df["timestamp"] >= pd.to_datetime(start_dt)
    if end_dt is not None:
        mask &= df["timestamp"] <= pd.to_datetime(end_dt)
    filtered_df = df[mask]

    if target_csv_file_path:
        filtered_df.to_csv(target_csv_file_path, index=False)

    power_metrics_info: dict[str, float] = {"mean_power": 0, "p95_power": 0, "p99_power": 0}

    if filtered_df.empty:
        return power_metrics_info

    power_consumptions = filtered_df.groupby("timestamp")["power_consumption"].sum().tolist()

    power_metrics_info["mean_power"] = round(np.mean(power_consumptions), 2)
    power_metrics_info["p95_power"] = round(np.percentile(power_consumptions, 95), 2)
    power_metrics_info["p99_power"] = round(np.percentile(power_consumptions, 99), 2)

    return power_metrics_info
