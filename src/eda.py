import polars as pl
import os

def run_eda(file_path: str):
    print("--- Phase 2: Exploratory Data Analysis ---")
    print(f"Loading dataset from: {file_path}")
    
    # 1. Load data shape (lazy loading makes this fast)
    lf = pl.scan_csv(file_path, infer_schema_length=10000, low_memory=True, ignore_errors=True)
    
    # Materialize a quick schema scan
    schema = lf.collect_schema()
    total_cols = len(schema)
    print(f"Schema inferred successfully. Total columns: {total_cols}")
    
    # 2. Count total rows
    print("Counting total rows...")
    total_rows = lf.select(pl.len()).collect().item()
    print(f"Total Rows: {total_rows:,}")
    
    # 3. Check target distribution (loan_status)
    print("\nTarget Variable (loan_status) Distribution:")
    status_counts = (
        lf.group_by("loan_status")
        .len()
        .sort("len", descending=True)
        .collect()
    )
    for row in status_counts.iter_rows():
        status = row[0] or "NULL"
        count = row[1]
        pct = (count / total_rows) * 100
        print(f"  - {status:45}: {count:10,} ({pct:6.2f}%)")
        
    # 4. Analyze missingness across columns
    print("\nAnalyzing missingness percentage across all columns...")
    null_counts = lf.select([pl.col(col).null_count().alias(col) for col in schema.names()]).collect()
    
    missing_report = []
    for col in schema.names():
        null_cnt = null_counts.item(0, col)
        missing_pct = (null_cnt / total_rows) * 100
        missing_report.append((col, null_cnt, missing_pct))
    
    # Sort columns by missingness descending (Python list sort uses reverse=True)
    missing_report.sort(key=lambda x: x[2], reverse=True)
    
    print("\nTop 15 columns with highest missingness:")
    for col, count, pct in missing_report[:15]:
        print(f"  - {col:40}: {count:10,} ({pct:6.2f}%)")
        
    high_missing_cols = [col for col, _, pct in missing_report if pct > 50]
    print(f"\nNumber of columns with >50% missing values: {len(high_missing_cols)}")
    
    # 5. Check basic stats of key features
    key_features = ["loan_amnt", "int_rate", "annual_inc", "dti", "fico_range_low", "fico_range_high"]
    
    # Ensure they are cast to numerical for proper describing if they are read as strings
    casted_cols = []
    for col in key_features:
        if col in schema.names():
            casted_cols.append(pl.col(col).cast(pl.Float64, strict=False))
            
    if casted_cols:
        print("\nSummary Statistics of Key Features:")
        stats = lf.select(casted_cols).collect().describe()
        
        # Safe printing to avoid Windows console UnicodeEncodeError
        # print header
        cols = stats.columns
        print(f"{'statistic':<15} | " + " | ".join(f"{c:<15}" for c in cols[1:]))
        print("-" * (15 + 3 + len(cols[1:]) * 18))
        for row in stats.iter_rows():
            stat_name = row[0]
            values = row[1:]
            formatted_vals = []
            for val in values:
                if val is None:
                    formatted_vals.append(f"{'None':<15}")
                elif isinstance(val, float):
                    formatted_vals.append(f"{val:<15.4f}")
                else:
                    formatted_vals.append(f"{str(val):<15}")
            print(f"{stat_name:<15} | " + " | ".join(formatted_vals))
        
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.config import RAW_DATA_PATH
    if os.path.exists(RAW_DATA_PATH):
        run_eda(RAW_DATA_PATH)
    else:
        print(f"Error: Dataset not found at {RAW_DATA_PATH}")
