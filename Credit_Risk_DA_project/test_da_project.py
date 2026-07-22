import os
import pandas as pd
import pytest

# Constants
PROJECT_DIR = r"C:\Projects\Credit_Risk_Analysis"
RESULTS_DIR = os.path.join(PROJECT_DIR, "Credit_Risk_DA_project", "results")
PLOTS_DIR = os.path.join(PROJECT_DIR, "Credit_Risk_DA_project", "plots")

def test_portfolio_summary():
    """Verify that portfolio summary is correctly generated and has reasonable values."""
    path = os.path.join(RESULTS_DIR, "portfolio_summary.csv")
    assert os.path.exists(path), f"File not found: {path}"
    
    df = pd.read_csv(path)
    required_cols = ["grade", "term", "total_loans", "total_loan_amnt", "avg_int_rate", "avg_dti", "avg_annual_inc", "default_rate_pct"]
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
        
    assert len(df) > 0
    # Interest rates should increase as grade gets riskier (A is lowest, G is highest)
    grade_a_rates = df[df["grade"] == "A"]["avg_int_rate"].mean()
    grade_g_rates = df[df["grade"] == "G"]["avg_int_rate"].mean()
    assert grade_a_rates < grade_g_rates, f"Grade A rates ({grade_a_rates}) should be less than Grade G rates ({grade_g_rates})"

def test_vintage_cohort_summary():
    """Verify that vintage cohort summary is correctly generated."""
    path = os.path.join(RESULTS_DIR, "vintage_cohort_summary.csv")
    assert os.path.exists(path), f"File not found: {path}"
    
    df = pd.read_csv(path)
    assert "cohort" in df.columns
    assert "default_rate_pct" in df.columns
    assert len(df) >= 40 # 2007 to 2018 is about 48 quarters

def test_dti_bucket_summary():
    """Verify that default rates are monotonic relative to DTI buckets."""
    path = os.path.join(RESULTS_DIR, "dti_bucket_summary.csv")
    assert os.path.exists(path), f"File not found: {path}"
    
    df = pd.read_csv(path)
    assert len(df) == 4
    
    # We expect default rates to increase as DTI increases:
    # '00-10' < '10-20' < '20-30' < '30+'
    df = df.set_index("dti_bucket").sort_index()
    rates = df["default_rate_pct"].tolist()
    
    # Check monotonic increase
    assert rates[0] < rates[1], f"Default rate should increase from 00-10 ({rates[0]}) to 10-20 ({rates[1]})"
    assert rates[1] < rates[2], f"Default rate should increase from 10-20 ({rates[1]}) to 20-30 ({rates[2]})"
    assert rates[2] < rates[3], f"Default rate should increase from 20-30 ({rates[2]}) to 30+ ({rates[3]})"

def test_monthly_forecasts():
    """Verify that monthly forecasts have consistent confidence intervals."""
    path = os.path.join(RESULTS_DIR, "monthly_forecasts.csv")
    assert os.path.exists(path), f"File not found: {path}"
    
    df = pd.read_csv(path)
    assert len(df) == 12 # exactly 12 forecasted months
    
    for idx, row in df.iterrows():
        # Check loan count boundaries
        assert row["loan_count_lower_ci"] <= row["loan_count_forecast"]
        assert row["loan_count_forecast"] <= row["loan_count_upper_ci"]
        
        # Check default rate boundaries (rates are expressed as decimals 0 to 1)
        assert row["default_rate_lower_ci"] <= row["default_rate_forecast"]
        assert row["default_rate_forecast"] <= row["default_rate_upper_ci"]
        assert 0.0 <= row["default_rate_forecast"] <= 1.0

def test_plots_exist():
    """Verify that all expected plots were generated."""
    plots = [
        "vintage_cohort_analysis.png",
        "volume_forecast.png",
        "default_rate_forecast.png",
        "dti_default_rates.png",
        "purpose_default_rates.png"
    ]
    for plot in plots:
        plot_path = os.path.join(PLOTS_DIR, plot)
        assert os.path.exists(plot_path), f"Plot not found: {plot_path}"
        assert os.path.getsize(plot_path) > 0, f"Plot is empty: {plot_path}"
