import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 16
})

# Constants
PROJECT_DIR = r"C:\Projects\Credit_Risk_Analysis"
RESULTS_DIR = os.path.join(PROJECT_DIR, "Credit_Risk_DA_project", "results")
PLOTS_DIR = os.path.join(PROJECT_DIR, "Credit_Risk_DA_project", "plots")

# Modern Palette colors
DARK_BLUE = "#1A365D"
TEAL = "#319795"
LIGHT_TEAL = "#E6FFFA"
ORANGE = "#DD6B20"
LIGHT_ORANGE = "#FFFAF0"
GRAY = "#718096"
CORAL = "#E53E3E"

def plot_vintage_cohorts():
    """Plot quarterly vintage default rates."""
    df = pd.read_csv(os.path.join(RESULTS_DIR, "vintage_cohort_summary.csv"))
    
    fig, ax1 = plt.subplots(figsize=(14, 6))
    
    # Plot volume as bar chart on primary axis
    color_bar = "#CBD5E0"
    ax1.bar(df["cohort"], df["total_loan_amnt"] / 1e6, color=color_bar, alpha=0.7, label="Loan Amount ($M)")
    ax1.set_xlabel("Origination Cohort (Quarter)", fontweight="bold")
    ax1.set_ylabel("Total Loan Amount ($ Millions)", color=GRAY, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor=GRAY)
    ax1.set_xticklabels(df["cohort"], rotation=90)
    
    # Create secondary axis for default rate line
    ax2 = ax1.twinx()
    ax2.plot(df["cohort"], df["default_rate_pct"], color=CORAL, linewidth=2.5, marker="o", markersize=4, label="Default Rate (%)")
    ax2.set_ylabel("Ultimate Default Rate (%)", color=CORAL, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor=CORAL)
    
    plt.title("Vintage Cohort Analysis: Total Origination Volume vs. Ultimate Default Rate", pad=20, fontweight="bold", color=DARK_BLUE)
    fig.tight_layout()
    
    # Save chart
    plt.savefig(os.path.join(PLOTS_DIR, "vintage_cohort_analysis.png"), dpi=300)
    plt.close()

def plot_forecasting():
    """Plot monthly volume and default rate forecasts."""
    df_hist = pd.read_csv(os.path.join(RESULTS_DIR, "monthly_historical_metrics.csv"))
    df_fc = pd.read_csv(os.path.join(RESULTS_DIR, "monthly_forecasts.csv"))
    
    # Parse dates
    df_hist["date"] = pd.to_datetime(df_hist["date"])
    df_fc["date"] = pd.to_datetime(df_fc["date"])
    
    # --- Chart 1: Volume Forecast ---
    plt.figure(figsize=(12, 6))
    plt.plot(df_hist["date"], df_hist["loan_count"], color=DARK_BLUE, label="Historical Volume", linewidth=2)
    plt.plot(df_fc["date"], df_fc["loan_count_forecast"], color=ORANGE, linestyle="--", label="12-Month Forecast", linewidth=2)
    plt.fill_between(
        df_fc["date"], 
        df_fc["loan_count_lower_ci"], 
        df_fc["loan_count_upper_ci"], 
        color=ORANGE, 
        alpha=0.15, 
        label="95% Confidence Interval"
    )
    plt.title("Loan Volume Trend and 12-Month Forecast", pad=15, fontweight="bold", color=DARK_BLUE)
    plt.xlabel("Date", fontweight="bold")
    plt.ylabel("Monthly Loan Count", fontweight="bold")
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "volume_forecast.png"), dpi=300)
    plt.close()
    
    # --- Chart 2: Default Rate Forecast ---
    plt.figure(figsize=(12, 6))
    plt.plot(df_hist["date"], df_hist["default_rate"] * 100, color=DARK_BLUE, label="Historical Default Rate", linewidth=2)
    plt.plot(df_fc["date"], df_fc["default_rate_forecast"] * 100, color=CORAL, linestyle="--", label="12-Month Forecast", linewidth=2)
    plt.fill_between(
        df_fc["date"], 
        df_fc["default_rate_lower_ci"] * 100, 
        df_fc["default_rate_upper_ci"] * 100, 
        color=CORAL, 
        alpha=0.15, 
        label="95% Confidence Interval"
    )
    plt.title("Portfolio Default Rate Trend and 12-Month Forecast", pad=15, fontweight="bold", color=DARK_BLUE)
    plt.xlabel("Date", fontweight="bold")
    plt.ylabel("Monthly Default Rate (%)", fontweight="bold")
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "default_rate_forecast.png"), dpi=300)
    plt.close()

def plot_dti_buckets():
    """Plot default rates by DTI bucket."""
    df = pd.read_csv(os.path.join(RESULTS_DIR, "dti_bucket_summary.csv"))
    
    plt.figure(figsize=(8, 5))
    bars = plt.bar(df["dti_bucket"], df["default_rate_pct"], color=TEAL, edgecolor="none", alpha=0.85, width=0.6)
    
    # Add values on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.8, f"{yval:.2f}%", ha="center", va="bottom", fontweight="semibold")
        
    plt.title("Ultimate Default Rate by Debt-to-Income (DTI) Bucket", pad=15, fontweight="bold", color=DARK_BLUE)
    plt.xlabel("DTI Bucket", fontweight="bold")
    plt.ylabel("Default Rate (%)", fontweight="bold")
    plt.ylim(0, max(df["default_rate_pct"]) + 5)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "dti_default_rates.png"), dpi=300)
    plt.close()

def plot_purpose():
    """Plot default rates by loan purpose."""
    df = pd.read_csv(os.path.join(RESULTS_DIR, "purpose_summary.csv"))
    # Keep top 10 categories for cleaner chart
    df = df.head(10)
    
    plt.figure(figsize=(10, 6))
    colors = [CORAL if x > 22 else TEAL for x in df["default_rate_pct"]]
    bars = plt.barh(df["purpose"], df["default_rate_pct"], color=colors, alpha=0.85, height=0.6)
    
    # Add values on right of bars
    for bar in bars:
        xval = bar.get_width()
        plt.text(xval + 0.5, bar.get_y() + bar.get_height()/2, f"{xval:.2f}%", ha="left", va="center", fontweight="semibold")
        
    plt.title("Top 10 Loan Purposes by Ultimate Default Rate", pad=15, fontweight="bold", color=DARK_BLUE)
    plt.xlabel("Default Rate (%)", fontweight="bold")
    plt.ylabel("Loan Purpose", fontweight="bold")
    plt.xlim(0, max(df["default_rate_pct"]) + 5)
    plt.gca().invert_yaxis() # Highest default rate on top
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "purpose_default_rates.png"), dpi=300)
    plt.close()

def main():
    os.makedirs(PLOTS_DIR, exist_ok=True)
    
    plot_vintage_cohorts()
    plot_forecasting()
    plot_dti_buckets()
    plot_purpose()
    
    print("Charts generated successfully in:", PLOTS_DIR)

if __name__ == "__main__":
    main()
