import os
import sys
import json
import logging
import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure src can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import PROCESSED_DATA_PATH, TARGET_COL, DATE_COL

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Scaling Parameters
BASE_SCORE = 600.0
BASE_ODDS = 50.0  # 50 Good to 1 Bad
PDO = 20.0

def calculate_scaling_parameters():
    """Solve for Factor and Offset using Points-to-Double-the-Odds (PDO)."""
    factor = PDO / np.log(2.0)
    offset = BASE_SCORE - factor * np.log(BASE_ODDS)
    return factor, offset

def generate_bin_label(rule, bin_key):
    """Generate human-readable labels for each feature bin."""
    if bin_key == "0" or bin_key == "Missing":
        return "Missing / Null"
    
    if rule["type"] == "numeric":
        edges = rule["edges"]
        idx = int(bin_key)
        n_edges = len(edges)
        
        if idx == 1:
            return f"<= {edges[1]:.2f}"
        elif idx == n_edges - 1:
            return f"> {edges[-2]:.2f}"
        else:
            return f"({edges[idx-1]:.2f}, {edges[idx]:.2f}]"
    else:
        # Categorical
        if bin_key == "Other":
            return "Other (Rare Categories)"
        return str(bin_key)

def build_scorecard(rules, factor, offset):
    """Assign point values to each feature bin using scaling parameters."""
    selected_features = rules["selected_features"]
    coefs = rules["logistic_regression"]["coefficients"]
    intercept = rules["logistic_regression"]["intercept"]
    N = len(selected_features)
    
    scorecard_points = {}
    scorecard_table = []
    
    logger.info("Scaling coefficients to scorecard points...")
    
    for feat in selected_features:
        coef_j = coefs[feat]
        woe_map = rules["woe_maps"][feat]
        rule = rules["binner_rules"][feat]
        
        scorecard_points[feat] = {}
        for bin_key, woe_val in woe_map.items():
            # Standard Scaling Formula:
            # Points = (-beta_j * WoE_ji - alpha/N) * Factor + Offset/N
            points = (-coef_j * woe_val - intercept / N) * factor + (offset / N)
            points_rounded = int(np.round(points))
            
            scorecard_points[feat][bin_key] = points_rounded
            
            # For output formatting
            label = generate_bin_label(rule, bin_key)
            scorecard_table.append({
                "Feature": feat,
                "Bin": bin_key,
                "Bin Label": label,
                "WoE": woe_val,
                "Points": points_rounded
            })
            
    return scorecard_points, scorecard_table

def calculate_scores(df: pl.DataFrame, scorecard_points, rules) -> pl.Series:
    """Score a Polars DataFrame using the generated scorecard integer points."""
    selected_features = rules["selected_features"]
    total_score = np.zeros(len(df), dtype=np.int32)
    
    for col in selected_features:
        col_data = df[col].to_numpy()
        is_null = df[col].is_null().to_numpy()
        rule = rules["binner_rules"][col]
        points_map = scorecard_points[col]
        
        # Determine bin assignments
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
                    
        # Map bin assignments to points
        col_points = np.zeros_like(col_data, dtype=np.int32)
        for idx, b in enumerate(bin_assignments):
            b_str = str(b)
            # Default to 0 points if not found
            col_points[idx] = points_map.get(b_str, 0)
            
        total_score += col_points
        
    return pl.Series("score", total_score)

def run_scorecard_generation():
    logger.info("Starting Phase 6: Scorecard Scaling & Distribution...")
    
    # 1. Load splits and rules
    splits_dir = os.path.join(os.path.dirname(PROCESSED_DATA_PATH), "splits")
    rules_path = os.path.join(os.path.dirname(PROCESSED_DATA_PATH), "scorecard_rules.json")
    
    with open(rules_path, "r") as f:
        rules = json.load(f)
        
    train = pl.read_parquet(os.path.join(splits_dir, "train.parquet"))
    val = pl.read_parquet(os.path.join(splits_dir, "val.parquet"))
    test = pl.read_parquet(os.path.join(splits_dir, "test.parquet"))
    
    # 2. Scaling Factors
    factor, offset = calculate_scaling_parameters()
    logger.info(f"Calibration Parameters: Factor = {factor:.4f}, Offset = {offset:.4f}")
    
    # 3. Build scorecard
    scorecard_points, scorecard_table = build_scorecard(rules, factor, offset)
    
    # Save scorecard to rules
    rules["scorecard_points"] = scorecard_points
    with open(rules_path, "w") as f:
        json.dump(rules, f, indent=2)
    logger.info("Saved scaled scorecard points to rules JSON.")
    
    # Save formatted scorecard as a CSV for easy download/inspection
    scorecard_df = pl.DataFrame(scorecard_table)
    scorecard_csv_path = os.path.join(os.path.dirname(PROCESSED_DATA_PATH), "scorecard.csv")
    scorecard_df.write_csv(scorecard_csv_path)
    logger.info(f"Saved formatted scorecard table to: {scorecard_csv_path}")
    
    # Print a preview of the scorecard
    print("\n--- SCORECARD PREVIEW ---")
    print(f"{'Feature':<25} | {'Bin Label':<40} | {'WoE':<10} | {'Points':<8}")
    print("-" * 90)
    for row in scorecard_table[:25]:
        print(f"{row['Feature']:<25} | {row['Bin Label']:<40} | {row['WoE']:<10.4f} | {row['Points']:<8}")
    print("... (see scorecard.csv for full table) ...\n")
    
    # 4. Score all datasets
    logger.info("Scoring all datasets...")
    train_scored = train.with_columns(calculate_scores(train, scorecard_points, rules))
    val_scored = val.with_columns(calculate_scores(val, scorecard_points, rules))
    test_scored = test.with_columns(calculate_scores(test, scorecard_points, rules))
    
    # Save scored test set
    scored_dir = os.path.join(os.path.dirname(PROCESSED_DATA_PATH), "scored")
    os.makedirs(scored_dir, exist_ok=True)
    test_scored.write_parquet(os.path.join(scored_dir, "test_scored.parquet"), compression="zstd")
    logger.info("Saved scored test set.")
    
    # 5. Print Credit Score distributions statistics
    logger.info("\n--- Credit Score Statistics on Out-of-Time Test Set (2018) ---")
    goods = test_scored.filter(pl.col(TARGET_COL) == 0)["score"].to_numpy()
    bads = test_scored.filter(pl.col(TARGET_COL) == 1)["score"].to_numpy()
    
    logger.info(f"Non-Defaulted (Good, Y=0): Mean = {goods.mean():.1f}, Median = {np.median(goods):.1f}, Std = {goods.std():.1f}, Range = [{goods.min()}, {goods.max()}]")
    logger.info(f"Defaulted (Bad, Y=1)    : Mean = {bads.mean():.1f}, Median = {np.median(bads):.1f}, Std = {bads.std():.1f}, Range = [{bads.min()}, {bads.max()}]")
    
    # 6. Plot Score Distributions
    plot_dir = os.path.join(os.path.dirname(os.path.dirname(PROCESSED_DATA_PATH)), "plots")
    os.makedirs(plot_dir, exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    sns.histplot(goods, color="green", label="Non-Defaulted (Good, Y=0)", kde=True, stat="density", alpha=0.4, bins=30)
    sns.histplot(bads, color="red", label="Defaulted (Bad, Y=1)", kde=True, stat="density", alpha=0.4, bins=30)
    plt.axvline(goods.mean(), color="darkgreen", linestyle="--", lw=2, label=f"Good Mean ({goods.mean():.1f})")
    plt.axvline(bads.mean(), color="darkred", linestyle="--", lw=2, label=f"Bad Mean ({bads.mean():.1f})")
    plt.xlabel("Credit Score")
    plt.ylabel("Density")
    plt.title("Credit Scorecard Distribution Comparison (2018 OOT)")
    plt.legend(loc="upper left")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(plot_dir, "score_distribution.png"), dpi=300)
    plt.close()
    
    logger.info("Score distribution plot saved successfully.")

if __name__ == "__main__":
    run_scorecard_generation()
