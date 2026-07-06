import os
import sys
import json
import logging
import pickle
import numpy as np
import polars as pl
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, roc_curve
from sklearn.calibration import calibration_curve
import lightgbm as lgb

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

def calculate_ks(y_true, y_prob):
    """Calculate Kolmogorov-Smirnov (KS) statistic using ROC curve values."""
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    ks = np.max(tpr - fpr)
    return float(ks)

def load_data():
    """Load train, val, test splits and scorecard rules."""
    splits_dir = os.path.join(os.path.dirname(PROCESSED_DATA_PATH), "splits")
    rules_path = os.path.join(os.path.dirname(PROCESSED_DATA_PATH), "scorecard_rules.json")
    
    logger.info("Loading split datasets...")
    train = pl.read_parquet(os.path.join(splits_dir, "train.parquet"))
    val = pl.read_parquet(os.path.join(splits_dir, "val.parquet"))
    test = pl.read_parquet(os.path.join(splits_dir, "test.parquet"))
    
    logger.info(f"Loaded splits - Train: {train.shape}, Val: {val.shape}, Test: {test.shape}")
    
    with open(rules_path, "r") as f:
        rules = json.load(f)
    
    return train, val, test, rules

def prepare_lgb_data(df: pl.DataFrame, features: list):
    """Encode categorical features for LightGBM and extract targets."""
    X = df.select(features).to_pandas()
    y = df[TARGET_COL].to_numpy()
    
    # Identify categoricals
    cat_features = []
    for col in X.columns:
        if X[col].dtype == object or isinstance(X[col].dtype, pd.CategoricalDtype) if 'pd' in sys.modules else False:
            X[col] = X[col].astype("category")
            cat_features.append(col)
        elif df[col].dtype == pl.String:
            X[col] = X[col].astype("category")
            cat_features.append(col)
            
    return X, y, cat_features

def run_training():
    logger.info("Starting Phase 5: Model Training & Evaluation...")
    
    # 1. Load Data
    train, val, test, rules = load_data()
    selected_features = rules["selected_features"]
    logger.info(f"Selected features for scorecard model: {selected_features}")
    
    # 2. Extract WoE features for Logistic Regression
    woe_features = [f"{col}_woe" for col in selected_features]
    
    X_train_woe = train.select(woe_features).to_numpy()
    y_train = train[TARGET_COL].to_numpy()
    
    X_val_woe = val.select(woe_features).to_numpy()
    y_val = val[TARGET_COL].to_numpy()
    
    X_test_woe = test.select(woe_features).to_numpy()
    y_test = test[TARGET_COL].to_numpy()
    
    # 3. Train Logistic Regression
    logger.info("Training Logistic Regression model on WoE features...")
    # C=1.0 L2 regularization is standard. We specify solver='lbfgs'
    lr_model = LogisticRegression(C=1.0, penalty="l2", solver="lbfgs", max_iter=1000, random_state=42)
    lr_model.fit(X_train_woe, y_train)
    
    # Save coefficients
    coefficients = {feat: float(coef) for feat, coef in zip(selected_features, lr_model.coef_[0])}
    intercept = float(lr_model.intercept_[0])
    
    logger.info("Logistic Regression model coefficients:")
    logger.info(f"  Intercept: {intercept:.4f}")
    for feat, coef in coefficients.items():
        logger.info(f"  {feat:25}: {coef:.4f}")
        
    # 4. Train LightGBM model on RAW features as a benchmark
    logger.info("Training LightGBM benchmark model on raw features...")
    import pandas as pd # Import pandas here as it is required for LightGBM category handling
    
    X_train_raw, _, cat_features = prepare_lgb_data(train, selected_features)
    X_val_raw, _, _ = prepare_lgb_data(val, selected_features)
    X_test_raw, _, _ = prepare_lgb_data(test, selected_features)
    
    train_data = lgb.Dataset(X_train_raw, label=y_train, categorical_feature=cat_features)
    val_data = lgb.Dataset(X_val_raw, label=y_val, reference=train_data, categorical_feature=cat_features)
    
    params = {
        "objective": "binary",
        "metric": "auc",
        "boosting_type": "gbdt",
        "n_estimators": 500,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "random_state": 42,
        "verbose": -1,
        "n_jobs": -1
    }
    
    # Train LGB
    lgb_model = lgb.train(
        params,
        train_data,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(50, verbose=False)]
    )
    
    # 5. Predict probabilities
    # Logistic Regression
    lr_prob_train = lr_model.predict_proba(X_train_woe)[:, 1]
    lr_prob_val = lr_model.predict_proba(X_val_woe)[:, 1]
    lr_prob_test = lr_model.predict_proba(X_test_woe)[:, 1]
    
    # LightGBM
    lgb_prob_train = lgb_model.predict(X_train_raw)
    lgb_prob_val = lgb_model.predict(X_val_raw)
    lgb_prob_test = lgb_model.predict(X_test_raw)
    
    # 6. Evaluation metrics on Test set (Out-of-Time 2018)
    logger.info("\n--- Model Evaluation on OOT Test Set (2018) ---")
    
    # AUC
    lr_auc = roc_auc_score(y_test, lr_prob_test)
    lgb_auc = roc_auc_score(y_test, lgb_prob_test)
    
    # PR-AUC
    lr_pr_precision, lr_pr_recall, _ = precision_recall_curve(y_test, lr_prob_test)
    lr_pr_auc = auc(lr_pr_recall, lr_pr_precision)
    
    lgb_pr_precision, lgb_pr_recall, _ = precision_recall_curve(y_test, lgb_prob_test)
    lgb_pr_auc = auc(lgb_pr_recall, lgb_pr_precision)
    
    # Gini
    lr_gini = 2 * lr_auc - 1
    lgb_gini = 2 * lgb_auc - 1
    
    # KS
    lr_ks = calculate_ks(y_test, lr_prob_test)
    lgb_ks = calculate_ks(y_test, lgb_prob_test)
    
    logger.info(f"Logistic Regression (WoE Scorecard Champion):")
    logger.info(f"  ROC-AUC  : {lr_auc:.4f}")
    logger.info(f"  Gini     : {lr_gini:.4f}")
    logger.info(f"  PR-AUC   : {lr_pr_auc:.4f}")
    logger.info(f"  KS Stat  : {lr_ks:.4f}")
    
    logger.info(f"LightGBM (ML Benchmark Ceiling):")
    logger.info(f"  ROC-AUC  : {lgb_auc:.4f}")
    logger.info(f"  Gini     : {lgb_gini:.4f}")
    logger.info(f"  PR-AUC   : {lgb_pr_auc:.4f}")
    logger.info(f"  KS Stat  : {lgb_ks:.4f}")
    
    # Save Logistic Regression model parameters in the scorecard rules JSON
    rules["logistic_regression"] = {
        "intercept": intercept,
        "coefficients": coefficients
    }
    
    rules_path = os.path.join(os.path.dirname(PROCESSED_DATA_PATH), "scorecard_rules.json")
    with open(rules_path, "w") as f:
        json.dump(rules, f, indent=2)
    logger.info(f"Updated scorecard rules with Logistic Regression parameters in {rules_path}")
    
    # Save the trained Logistic Regression model
    model_dir = os.path.join(os.path.dirname(PROCESSED_DATA_PATH), "models")
    os.makedirs(model_dir, exist_ok=True)
    with open(os.path.join(model_dir, "logistic_model.pkl"), "wb") as f:
        pickle.dump(lr_model, f)
    logger.info(f"Saved Logistic Regression pickle model to: {model_dir}")
    
    # 7. Generate comparison plots
    plot_dir = os.path.join(os.path.dirname(os.path.dirname(PROCESSED_DATA_PATH)), "plots")
    os.makedirs(plot_dir, exist_ok=True)
    logger.info(f"Saving comparison plots to: {plot_dir}")
    
    # Plot ROC curves
    plt.figure(figsize=(8, 6))
    lr_fpr, lr_tpr, _ = roc_curve(y_test, lr_prob_test)
    lgb_fpr, lgb_tpr, _ = roc_curve(y_test, lgb_prob_test)
    plt.plot(lr_fpr, lr_tpr, label=f"Logistic Regression (AUC = {lr_auc:.3f}, Gini = {lr_gini:.3f})", lw=2)
    plt.plot(lgb_fpr, lgb_tpr, label=f"LightGBM (AUC = {lgb_auc:.3f}, Gini = {lgb_gini:.3f})", lw=2, linestyle="--")
    plt.plot([0, 1], [0, 1], color="navy", linestyle=":")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve Comparison on Out-of-Time Test Set (2018)")
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(plot_dir, "roc_curve_comparison.png"), dpi=300)
    plt.close()
    
    # Plot Calibration curves
    plt.figure(figsize=(8, 6))
    lr_prob_true, lr_prob_pred = calibration_curve(y_test, lr_prob_test, n_bins=10)
    lgb_prob_true, lgb_prob_pred = calibration_curve(y_test, lgb_prob_test, n_bins=10)
    plt.plot(lr_prob_pred, lr_prob_true, marker="o", label="Logistic Regression", lw=2)
    plt.plot(lgb_prob_pred, lgb_prob_true, marker="s", label="LightGBM", lw=2, linestyle="--")
    plt.plot([0, 1], [0, 1], color="gray", linestyle=":")
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("True Probability in Bin")
    plt.title("Calibration Curves Comparison (Reliability)")
    plt.legend(loc="upper left")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(plot_dir, "calibration_curve_comparison.png"), dpi=300)
    plt.close()
    
    # Plot Precision-Recall curves
    plt.figure(figsize=(8, 6))
    plt.plot(lr_pr_recall, lr_pr_precision, label=f"Logistic Regression (PR-AUC = {lr_pr_auc:.3f})", lw=2)
    plt.plot(lgb_pr_recall, lgb_pr_precision, label=f"LightGBM (PR-AUC = {lgb_pr_auc:.3f})", lw=2, linestyle="--")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve Comparison")
    plt.legend(loc="lower left")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(plot_dir, "pr_curve_comparison.png"), dpi=300)
    plt.close()
    
    logger.info("Plots saved successfully.")

if __name__ == "__main__":
    run_training()
