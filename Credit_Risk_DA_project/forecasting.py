import os
import sys
import logging
from pathlib import Path
import polars as pl
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants — resolved dynamically
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
PROCESSED_DATA_PATH = os.path.join(PROJECT_DIR, "Source", "processed_data.parquet")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "Credit_Risk_DA_project", "results")

def prepare_monthly_series() -> pd.DataFrame:
    """Load data and aggregate to monthly series."""
    logger.info("Loading and aggregating data to monthly series...")
    
    # Load processed parquet using Polars
    lf = pl.scan_parquet(PROCESSED_DATA_PATH)
    
    # Extract year and month, then group
    df_monthly = (
        lf.with_columns([
            pl.col("issue_d").dt.year().alias("year"),
            pl.col("issue_d").dt.month().alias("month")
        ])
        .group_by(["year", "month"])
        .agg([
            pl.len().alias("loan_count"),
            pl.col("loan_amnt").sum().alias("total_loan_amnt"),
            pl.col("target").mean().alias("default_rate")
        ])
        .collect()
    )
    
    # Convert to Pandas for easier time series index manipulation
    pdf = df_monthly.to_pandas()
    
    # Create a proper datetime column
    pdf["date"] = pd.to_datetime(pdf[["year", "month"]].assign(day=1))
    pdf = pdf.sort_values("date").reset_index(drop=True)
    
    return pdf

def build_features(df: pd.DataFrame, is_train: bool = True, num_forecast_periods: int = 12) -> tuple:
    """Build trend and seasonal features for regression."""
    if is_train:
        n_samples = len(df)
        t = np.arange(n_samples).reshape(-1, 1)
        months = df["month"].values
    else:
        # Generate future time indices and months
        last_t = len(df) - 1
        t = np.arange(last_t + 1, last_t + 1 + num_forecast_periods).reshape(-1, 1)
        
        last_date = df["date"].max()
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=num_forecast_periods, freq="MS")
        months = future_dates.month
        
    # Create one-hot encoded seasonal dummies (months 1-12)
    seasonal_dummies = np.zeros((len(t), 12))
    for i, m in enumerate(months):
        seasonal_dummies[i, m - 1] = 1.0
        
    # Combine trend and seasonal features
    # We drop the first month's dummy to avoid the dummy variable trap
    X = np.hstack([t, seasonal_dummies[:, 1:]])
    return X, t

def forecast_series(df: pd.DataFrame, target_col: str, num_forecast_periods: int = 12) -> pd.DataFrame:
    """Forecast a target series using Ridge Regression (trend + seasonality)."""
    logger.info(f"Fitting forecasting model for: {target_col}...")
    
    X_train, t_train = build_features(df, is_train=True)
    y_train = df[target_col].values
    
    # Use Ridge regression for stability
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    
    # Fit stats
    y_pred = model.predict(X_train)
    residuals = y_train - y_pred
    rmse = np.sqrt(np.mean(residuals ** 2))
    logger.info(f"Model RMSE on historical data: {rmse:.4f}")
    
    # Forecast future values
    X_forecast, t_forecast = build_features(df, is_train=False, num_forecast_periods=num_forecast_periods)
    y_forecast = model.predict(X_forecast)
    
    # Ensure default rates don't fall below zero
    if "rate" in target_col:
        y_forecast = np.clip(y_forecast, 0.0, 1.0)
        
    # Calculate 95% Confidence Intervals
    # CI = Forecast +/- 1.96 * RMSE
    ci_margin = 1.96 * rmse
    lower_bound = y_forecast - ci_margin
    upper_bound = y_forecast + ci_margin
    
    if "rate" in target_col:
        lower_bound = np.clip(lower_bound, 0.0, 1.0)
        upper_bound = np.clip(upper_bound, 0.0, 1.0)
        
    # Reconstruct future dates
    last_date = df["date"].max()
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=num_forecast_periods, freq="MS")
    
    # Combine into dataframe
    df_fc = pd.DataFrame({
        "date": future_dates,
        f"{target_col}_forecast": y_forecast,
        f"{target_col}_lower_ci": lower_bound,
        f"{target_col}_upper_ci": upper_bound
    })
    
    return df_fc

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Aggregate data
    df_monthly = prepare_monthly_series()
    
    # Forecast monthly loan count (volume)
    df_volume_fc = forecast_series(df_monthly, "loan_count", num_forecast_periods=12)
    
    # Forecast monthly default rate
    df_default_fc = forecast_series(df_monthly, "default_rate", num_forecast_periods=12)
    
    # Merge forecasts
    df_all_fc = pd.merge(df_volume_fc, df_default_fc, on="date")
    
    # Format date for saving
    df_monthly["date"] = df_monthly["date"].dt.strftime("%Y-%m-%d")
    df_all_fc["date"] = df_all_fc["date"].dt.strftime("%Y-%m-%d")
    
    # Save results to CSV
    logger.info(f"Saving monthly aggregated data and forecasts to: {OUTPUT_DIR}")
    df_monthly.to_csv(os.path.join(OUTPUT_DIR, "monthly_historical_metrics.csv"), index=False)
    df_all_fc.to_csv(os.path.join(OUTPUT_DIR, "monthly_forecasts.csv"), index=False)
    
    logger.info("Forecasting pipeline completed successfully.")

if __name__ == "__main__":
    main()
