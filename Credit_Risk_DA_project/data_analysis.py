import os
import sys
import logging
from pathlib import Path
import polars as pl

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

def analyze_portfolio(ctx: pl.SQLContext) -> pl.DataFrame:
    """Analyze loan performance by grade and term."""
    logger.info("Analyzing loan portfolio by grade and term...")
    query = """
    SELECT 
        grade,
        term,
        COUNT(*) as total_loans,
        SUM(loan_amnt) as total_loan_amnt,
        ROUND(AVG(int_rate), 2) as avg_int_rate,
        ROUND(AVG(dti), 2) as avg_dti,
        ROUND(AVG(annual_inc), 2) as avg_annual_inc,
        ROUND(AVG(target) * 100, 2) as default_rate_pct
    FROM loans
    GROUP BY grade, term
    ORDER BY grade, term
    """
    return ctx.execute(query).collect()

def analyze_vintage_cohorts(ctx: pl.SQLContext) -> pl.DataFrame:
    """Analyze default rates by quarterly origination cohorts (vintages)."""
    logger.info("Analyzing quarterly vintage cohorts...")
    
    # In Polars SQL, we can extract year and calculate quarter using string/date functions
    # issue_d is a Date column, so we can use date functions if supported, or register a view
    # Let's project year and quarter first using Polars expressions or SQL functions.
    # Note: Polars SQL supports EXTRACT(YEAR FROM date) and EXTRACT(MONTH FROM date)
    query = """
    WITH cohort_data AS (
        SELECT 
            EXTRACT(YEAR FROM issue_d) as issue_year,
            EXTRACT(MONTH FROM issue_d) as issue_month,
            CASE 
                WHEN EXTRACT(MONTH FROM issue_d) IN (1, 2, 3) THEN 'Q1'
                WHEN EXTRACT(MONTH FROM issue_d) IN (4, 5, 6) THEN 'Q2'
                WHEN EXTRACT(MONTH FROM issue_d) IN (7, 8, 9) THEN 'Q3'
                ELSE 'Q4'
            END as issue_quarter,
            loan_amnt,
            target
        FROM loans
    )
    SELECT 
        CAST(issue_year AS VARCHAR) || '-' || issue_quarter as cohort,
        COUNT(*) as total_loans,
        SUM(loan_amnt) as total_loan_amnt,
        ROUND(AVG(target) * 100, 2) as default_rate_pct
    FROM cohort_data
    GROUP BY issue_year, issue_quarter
    ORDER BY issue_year, issue_quarter
    """
    return ctx.execute(query).collect()

def analyze_dti_buckets(ctx: pl.SQLContext) -> pl.DataFrame:
    """Analyze default rates across different DTI ranges."""
    logger.info("Analyzing performance by DTI buckets...")
    query = """
    WITH bucketed_data AS (
        SELECT 
            CASE 
                WHEN dti < 10 THEN '00-10'
                WHEN dti >= 10 AND dti < 20 THEN '10-20'
                WHEN dti >= 20 AND dti < 30 THEN '20-30'
                ELSE '30+'
            END as dti_bucket,
            target
        FROM loans
    )
    SELECT 
        dti_bucket,
        COUNT(*) as total_loans,
        ROUND(AVG(target) * 100, 2) as default_rate_pct
    FROM bucketed_data
    GROUP BY dti_bucket
    ORDER BY dti_bucket
    """
    return ctx.execute(query).collect()

def analyze_purpose(ctx: pl.SQLContext) -> pl.DataFrame:
    """Analyze default rates and volumes by loan purpose."""
    logger.info("Analyzing performance by loan purpose...")
    query = """
    SELECT 
        purpose,
        COUNT(*) as total_loans,
        SUM(loan_amnt) as total_loan_amnt,
        ROUND(AVG(int_rate), 2) as avg_int_rate,
        ROUND(AVG(target) * 100, 2) as default_rate_pct
    FROM loans
    GROUP BY purpose
    ORDER BY default_rate_pct DESC
    """
    return ctx.execute(query).collect()

def main():
    if not os.path.exists(PROCESSED_DATA_PATH):
        logger.error(f"Processed dataset not found at {PROCESSED_DATA_PATH}. Please run the ETL pipeline first.")
        sys.exit(1)
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load dataset lazily
    logger.info(f"Loading dataset from {PROCESSED_DATA_PATH}...")
    lf = pl.scan_parquet(PROCESSED_DATA_PATH)
    
    # Register in SQLContext
    ctx = pl.SQLContext()
    ctx.register("loans", lf)
    
    # Run analysis
    df_portfolio = analyze_portfolio(ctx)
    df_vintage = analyze_vintage_cohorts(ctx)
    df_dti = analyze_dti_buckets(ctx)
    df_purpose = analyze_purpose(ctx)
    
    # Save results to CSV
    logger.info(f"Saving analytical tables to: {OUTPUT_DIR}")
    df_portfolio.write_csv(os.path.join(OUTPUT_DIR, "portfolio_summary.csv"))
    df_vintage.write_csv(os.path.join(OUTPUT_DIR, "vintage_cohort_summary.csv"))
    df_dti.write_csv(os.path.join(OUTPUT_DIR, "dti_bucket_summary.csv"))
    df_purpose.write_csv(os.path.join(OUTPUT_DIR, "purpose_summary.csv"))
    
    logger.info("Data analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()
