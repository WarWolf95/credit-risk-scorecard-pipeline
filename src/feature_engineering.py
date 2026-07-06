import os
import sys
import json
import logging
import numpy as np
import polars as pl

# Ensure src can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import PROCESSED_DATA_PATH, APPLICATION_COLS, TARGET_COL, DATE_COL

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Exclude earliest_cr_line date from binning, replace it with months_since_earliest_cr_line
FEATURES_TO_BIN = [c for c in APPLICATION_COLS if c != "earliest_cr_line"] + ["mths_since_earliest_cr_line"]

class FeatureBinner:
    def __init__(self, n_bins: int = 10, min_iv: float = 0.02, max_iv: float = 0.5):
        self.n_bins = n_bins
        self.min_iv = min_iv
        self.max_iv = max_iv
        self.binner_rules = {}  # Store binning edges and categories
        self.woe_maps = {}      # Store bin index/category -> WoE value
        self.iv_report = {}     # Store total IV for each feature
        self.selected_features = []

    def fit(self, df: pl.DataFrame, target_col: str):
        logger.info("Fitting FeatureBinner on training data...")
        
        y = df[target_col].to_numpy()
        
        for col in FEATURES_TO_BIN:
            if col not in df.columns:
                logger.warning(f"Feature {col} not found in training dataset. Skipping.")
                continue
                
            dtype = df[col].dtype
            col_data = df[col].to_numpy()
            
            # Identify missing indices
            is_null = df[col].is_null().to_numpy()
            non_null_data = col_data[~is_null]
            
            # --- Binning Phase ---
            if dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32):
                # Numeric column
                if len(non_null_data) == 0:
                    # All nulls
                    bin_edges = []
                    bin_assignments = np.zeros_like(col_data, dtype=np.int32)
                else:
                    # Quantile binning on non-null values
                    quantiles = np.percentile(non_null_data, np.linspace(0, 100, self.n_bins + 1))
                    bin_edges = np.unique(quantiles).tolist()
                    
                    # If only 1 edge (constant), fallback to simple bounds
                    if len(bin_edges) < 2:
                        bin_edges = [non_null_data.min(), non_null_data.max()]
                        if bin_edges[0] == bin_edges[1]:
                            bin_edges[1] += 1.0 # break tie
                            
                    # Assign bins (1 to N, 0 is reserved for Missing)
                    bin_assignments = np.zeros_like(col_data, dtype=np.int32)
                    assigned_non_null = np.digitize(non_null_data, bin_edges[1:-1]) + 1
                    bin_assignments[~is_null] = assigned_non_null
                    
                self.binner_rules[col] = {
                    "type": "numeric",
                    "edges": bin_edges
                }
            else:
                # Categorical column (String)
                # Group rare categories (<1% frequency)
                val_counts = df[col].value_counts()
                total_rows = len(df)
                keep_categories = []
                
                for row in val_counts.iter_rows():
                    cat = row[0]
                    count = row[1]
                    if cat is not None and cat != "" and (count / total_rows) >= 0.01:
                        keep_categories.append(str(cat))
                        
                bin_assignments = np.empty_like(col_data, dtype=object)
                for idx, val in enumerate(col_data):
                    if is_null[idx] or val == "":
                        bin_assignments[idx] = "Missing"
                    elif str(val) in keep_categories:
                        bin_assignments[idx] = str(val)
                    else:
                        bin_assignments[idx] = "Other"
                        
                self.binner_rules[col] = {
                    "type": "categorical",
                    "keep_categories": keep_categories
                }

            # --- Calculate WoE and IV per Bin ---
            unique_bins = np.unique(bin_assignments)
            bin_woe = {}
            feature_iv = 0.0
            
            # Counts for each bin
            bin_counts = {}
            for b in unique_bins:
                mask = (bin_assignments == b)
                g_i = np.sum(y[mask] == 0)
                b_i = np.sum(y[mask] == 1)
                bin_counts[b] = (g_i, b_i)
                
            # Compute total smoothed goods and bads across all bins
            g_total_smooth = sum(g + 0.5 for g, b in bin_counts.values())
            b_total_smooth = sum(b + 0.5 for g, b in bin_counts.values())
            
            for b, (g_i, b_i) in bin_counts.items():
                g_i_smooth = g_i + 0.5
                b_i_smooth = b_i + 0.5
                
                prop_good = g_i_smooth / g_total_smooth
                prop_bad = b_i_smooth / b_total_smooth
                
                woe_i = np.log(prop_good / prop_bad)
                bin_woe[str(b)] = float(woe_i)
                
                # Add to total IV
                feature_iv += (prop_good - prop_bad) * woe_i
                
            self.woe_maps[col] = bin_woe
            self.iv_report[col] = float(feature_iv)
            
            logger.info(f"Feature: {col:25} | Type: {self.binner_rules[col]['type']:11} | IV: {feature_iv:.4f}")

    def transform(self, df: pl.DataFrame) -> pl.DataFrame:
        """Transform raw columns into their WoE values."""
        transformed_cols = []
        
        for col in FEATURES_TO_BIN:
            if col not in self.binner_rules:
                continue
                
            col_data = df[col].to_numpy()
            is_null = df[col].is_null().to_numpy()
            rule = self.binner_rules[col]
            woe_map = self.woe_maps[col]
            
            transformed_woe = np.zeros_like(col_data, dtype=np.float64)
            
            if rule["type"] == "numeric":
                edges = rule["edges"]
                if not edges:
                    bin_assignments = np.zeros_like(col_data, dtype=np.int32)
                else:
                    bin_assignments = np.zeros_like(col_data, dtype=np.int32)
                    non_null_data = col_data[~is_null]
                    assigned_non_null = np.digitize(non_null_data, edges[1:-1]) + 1
                    bin_assignments[~is_null] = assigned_non_null
            else:
                keep_categories = rule["keep_categories"]
                bin_assignments = np.empty_like(col_data, dtype=object)
                for idx, val in enumerate(col_data):
                    if is_null[idx] or val == "":
                        bin_assignments[idx] = "Missing"
                    elif str(val) in keep_categories:
                        bin_assignments[idx] = str(val)
                    else:
                        bin_assignments[idx] = "Other"
            
            # Map assigned bins to WoE values
            for idx, b in enumerate(bin_assignments):
                b_str = str(b)
                transformed_woe[idx] = woe_map.get(b_str, 0.0)
                
            transformed_cols.append(pl.Series(f"{col}_woe", transformed_woe))
            
        # Return new DataFrame containing keys, target, and transformed columns
        key_cols = [DATE_COL, TARGET_COL]
        # Include original features as well (so LightGBM has access to them)
        original_cols = [pl.col(c) for c in FEATURES_TO_BIN]
        
        # Select key columns and original columns first, then add the transformed columns
        return df.select(key_cols + FEATURES_TO_BIN).with_columns(transformed_cols)

    def select_features(self, df_woe: pl.DataFrame):
        """Perform feature selection based on IV and correlation."""
        logger.info("Performing feature selection based on IV and correlation...")
        
        candidate_cols = [
            col for col, iv in self.iv_report.items()
            if self.min_iv <= iv <= self.max_iv
        ]
        
        candidate_cols.sort(key=lambda x: self.iv_report[x], reverse=True)
        logger.info(f"Candidates satisfying IV limits [{self.min_iv}, {self.max_iv}]: {len(candidate_cols)}")
        
        # Compute correlation matrix on train candidates (convert to pandas for correlation)
        woe_col_names = [f"{c}_woe" for c in candidate_cols]
        df_pd = df_woe.select(woe_col_names).to_pandas()
        corr_matrix = df_pd.corr().abs()
        
        selected = []
        for col in candidate_cols:
            woe_col = f"{col}_woe"
            is_correlated = False
            for sel_col in selected:
                sel_woe_col = f"{sel_col}_woe"
                if corr_matrix.loc[woe_col, sel_woe_col] > 0.7:
                    logger.info(f"Dropping {col} (IV: {self.iv_report[col]:.4f}) due to correlation with {sel_col} (IV: {self.iv_report[sel_col]:.4f})")
                    is_correlated = True
                    break
            if not is_correlated:
                selected.append(col)
                
        self.selected_features = selected
        logger.info(f"Features selected after correlation check: {len(self.selected_features)}")
        for col in self.selected_features:
            logger.info(f"  - {col}: IV = {self.iv_report[col]:.4f}")

    def save_rules(self, path: str):
        rules = {
            "binner_rules": self.binner_rules,
            "woe_maps": self.woe_maps,
            "iv_report": self.iv_report,
            "selected_features": self.selected_features
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(rules, f, indent=2)
        logger.info(f"Binner rules and scorecard config saved to: {path}")


def run_feature_engineering():
    logger.info("Starting Phase 4: Feature Engineering...")
    
    logger.info(f"Loading preprocessed dataset from: {PROCESSED_DATA_PATH}")
    df = pl.read_parquet(PROCESSED_DATA_PATH)
    
    # Pre-calculate mths_since_earliest_cr_line feature
    logger.info("Pre-calculating credit history length (mths_since_earliest_cr_line)...")
    df = df.with_columns(
        ((pl.col("issue_d") - pl.col("earliest_cr_line")).dt.total_days() / 30.4375)
        .cast(pl.Float64)
        .alias("mths_since_earliest_cr_line")
    )
    
    # Chronological split
    logger.info("Splitting dataset chronologically:")
    df_train = df.filter(pl.col(DATE_COL) < pl.date(2017, 1, 1))
    df_val = df.filter((pl.col(DATE_COL) >= pl.date(2017, 1, 1)) & (pl.col(DATE_COL) < pl.date(2018, 1, 1)))
    df_test = df.filter(pl.col(DATE_COL) >= pl.date(2018, 1, 1))
    
    logger.info(f"  - Train split (before 2017): {df_train.shape}")
    logger.info(f"  - Validation split (2017) : {df_val.shape}")
    logger.info(f"  - Test split (2018 OOT)    : {df_test.shape}")
    
    # Fit Binner on Train set
    binner = FeatureBinner(n_bins=10, min_iv=0.02, max_iv=0.5)
    binner.fit(df_train, TARGET_COL)
    
    # Transform all splits to WoE values
    logger.info("Transforming datasets to WoE values...")
    df_train_woe = binner.transform(df_train)
    df_val_woe = binner.transform(df_val)
    df_test_woe = binner.transform(df_test)
    
    # Perform feature selection based on Train WoE
    binner.select_features(df_train_woe)
    
    # Save rules
    rules_path = os.path.join(os.path.dirname(PROCESSED_DATA_PATH), "scorecard_rules.json")
    binner.save_rules(rules_path)
    
    # Save splits
    logger.info("Saving split datasets with WoE columns...")
    output_dir = os.path.join(os.path.dirname(PROCESSED_DATA_PATH), "splits")
    os.makedirs(output_dir, exist_ok=True)
    
    df_train_woe.write_parquet(os.path.join(output_dir, "train.parquet"), compression="zstd")
    df_val_woe.write_parquet(os.path.join(output_dir, "val.parquet"), compression="zstd")
    df_test_woe.write_parquet(os.path.join(output_dir, "test.parquet"), compression="zstd")
    logger.info("Split datasets saved successfully.")

if __name__ == "__main__":
    run_feature_engineering()
