import os
import sys
import logging
import polars as pl

# Ensure src can import config even if executed directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import RAW_DATA_PATH, PROCESSED_DATA_PATH, APPLICATION_COLS, TARGET_COL, DATE_COL, TARGET_MAPPING

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_raw_data(file_path: str) -> pl.LazyFrame:
    """Lazily scan raw CSV data."""
    logger.info(f"Scanning raw CSV dataset from: {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file not found at {file_path}")
    
    # We use infer_schema_length=100000 to ensure robust type inference
    return pl.scan_csv(
        file_path,
        infer_schema_length=100000,
        low_memory=True,
        ignore_errors=True
    )

def preprocess_data(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Clean, filter, and preprocess features and target."""
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Filter out excluded loan statuses
    valid_statuses = list(TARGET_MAPPING.keys())
    lf = lf.filter(pl.col("loan_status").is_in(valid_statuses))
    
    # 2. Build expressions for data transformations
    
    # Map target variable
    target_expr = pl.col("loan_status").replace_strict(TARGET_MAPPING, default=None).cast(pl.Int8).alias(TARGET_COL)
    
    # Clean term (e.g. " 36 months" -> 36)
    term_expr = (
        pl.col("term")
        .str.strip_chars()
        .str.replace(" months", "", literal=True)
        .cast(pl.Int32, strict=False)
    )
    
    # Clean emp_length (e.g. "10+ years" -> 10, "< 1 year" -> 0, etc.)
    emp_length_expr = (
        pl.col("emp_length")
        .str.strip_chars()
        .str.replace("10+ years", "10", literal=True)
        .str.replace("< 1 year", "0", literal=True)
        .str.replace(" years", "", literal=True)
        .str.replace(" year", "", literal=True)
        .cast(pl.Int32, strict=False)
    )
    
    # Parse date strings to date types
    issue_d_expr = pl.col("issue_d").str.strptime(pl.Date, format="%b-%Y", strict=False)
    earliest_cr_line_expr = pl.col("earliest_cr_line").str.strptime(pl.Date, format="%b-%Y", strict=False)
    
    # Clean revol_util percentage (if String, strip '%' and cast; else cast directly)
    schema = lf.collect_schema()
    if schema.get("revol_util") == pl.String:
        revol_util_expr = (
            pl.col("revol_util")
            .str.strip_chars()
            .str.replace("%", "", literal=True)
            .cast(pl.Float64, strict=False)
        )
    else:
        revol_util_expr = pl.col("revol_util").cast(pl.Float64)
        
    # 3. Apply transformations using with_columns
    lf = lf.with_columns([
        target_expr,
        term_expr,
        emp_length_expr,
        issue_d_expr,
        earliest_cr_line_expr,
        revol_util_expr
    ])
    
    # 4. Filter out any remaining rows with null targets or issue dates
    lf = lf.filter(pl.col(TARGET_COL).is_not_null() & pl.col(DATE_COL).is_not_null())
    
    # 5. Select output columns
    output_cols = [DATE_COL, TARGET_COL] + APPLICATION_COLS
    lf = lf.select(output_cols)
    
    return lf

def run_etl_pipeline():
    """Run the end-to-end data ETL pipeline and save as parquet."""
    logger.info("Executing ETL pipeline...")
    
    try:
        # Load
        lf = load_raw_data(RAW_DATA_PATH)
        
        # Preprocess
        lf_clean = preprocess_data(lf)
        
        # Collect & Materialize
        logger.info("Collecting LazyFrame and executing processing in memory (this may take a few moments)...")
        df_clean = lf_clean.collect()
        
        logger.info(f"ETL completed successfully. Cleaned data shape: {df_clean.shape}")
        
        # Log target distribution
        target_counts = df_clean["target"].value_counts()
        logger.info("Target distribution after preprocessing:")
        for row in target_counts.iter_rows():
            val, count = row[0], row[1]
            pct = (count / df_clean.height) * 100
            logger.info(f"  - Target {val}: {count:,} ({pct:.2f}%)")
            
        # Ensure target directory exists
        os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
        
        # Save to parquet
        logger.info(f"Saving preprocessed dataset to: {PROCESSED_DATA_PATH}")
        df_clean.write_parquet(PROCESSED_DATA_PATH, compression="zstd")
        logger.info("Data saved successfully.")
        
    except Exception as e:
        logger.error(f"ETL pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    run_etl_pipeline()
