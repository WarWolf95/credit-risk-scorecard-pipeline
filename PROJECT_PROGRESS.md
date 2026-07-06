# Project Progress Tracker

This document tracks the progress of the Credit Risk Analysis & Scorecard Modeling project. Steps are marked as:
*   `[ ]` Not Started
*   `[/]` In Progress
*   `[x]` Completed

---

## Progress Summary

### [x] Phase 1: Project Initialization & Core Documentation
*   [x] Set up base project directory structure
*   [x] Define dependency requirements in `requirements.txt`
*   [x] Write comprehensive educational `README.md`
*   [x] Create `PROJECT_PROGRESS.md` (this file)
*   [x] Create `PROJECT_CAPSULE.md` for context saving
*   [x] Wait for user approval to proceed to Phase 2

### [x] Phase 2: Environment & Data Exploration
*   [x] Install packages from `requirements.txt`
*   [x] Write basic EDA script to check raw data dimensions, columns, and target counts
*   [x] Evaluate distributions of crucial variables (FICO, DTI, Income, Loan Amount)
*   [x] Document data quality findings (missingness, cardinality)


### [x] Phase 3: Data Loading & Preprocessing (ETL)
*   [x] Write `src/config.py` defining variables (keep vs drop to prevent data leakage)
*   [x] Write `src/data_loader.py` using Polars to load, clean, and filter the dataset
*   [x] Define and extract target label (1 = Default/Charged Off, 0 = Fully Paid)
*   [x] Exclude current and irrelevant loans
*   [x] Run ETL pipeline and save intermediate clean dataset (or cache it)

### [x] Phase 4: Feature Engineering & Validation Splits
*   [x] Implement chronological validation splitting in `src/feature_engineering.py` (train/validation/test based on `issue_d`)
*   [x] Implement fine/coarse binning strategy for numeric features
*   [x] Compute Weight of Evidence (WoE) and Information Value (IV) for each feature
*   [x] Select top features based on IV and correlation analysis
*   [x] Transform datasets to WoE values

### [x] Phase 5: Model Training & Evaluation
*   [x] Implement baseline Logistic Regression model on WoE-transformed features in `src/train.py`
*   [x] Implement a LightGBM model on raw features as a benchmark
*   [x] Evaluate both models on test set using ROC-AUC, PR-AUC, Gini, and Kolmogorov-Smirnov (KS) statistic
*   [x] Plot comparison curves (ROC, Calibration, Precision-Recall) to `plots/` folder
*   [x] Document metrics and select the champion model

### [x] Phase 6: Scorecard Scaling & Distribution
*   [x] Implement scaling math (Points to Double the Odds) in `src/scorecard.py`
*   [x] Map Logistic Regression coefficients and WoE values to score points
*   [x] Format the scorecard as a tabular production-ready output
*   [x] Generate and plot score distribution comparison for defaulted vs non-defaulted loans

### [x] Phase 7: Productionization & Testing
*   [x] Write basic unit tests in `tests/` directory (e.g. testing scorecard scaling consistency, data loader constraints)
*   [x] Add type hints, logging, and performance measurements (production level)
*   [x] Write final summary walk-through and upload instructions
