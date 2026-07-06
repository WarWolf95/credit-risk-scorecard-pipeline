# Credit Risk Project Capsule

This capsule acts as the core memory for the Credit Risk Analysis & Scorecard Modeling project. If you are a new LLM or agent resuming this project, read this file first to understand the current state, constraints, and next steps.

---

## 1. Project Overview & Context
*   **Project Path**: `C:\Projects\Credit_Risk_Analysis`
*   **Dataset**: `Source/accepted_2007_to_2018Q4.csv` (1.56 GB, 2,260,701 rows, 151 columns).
*   **Domain**: Credit Risk Modeling (Probability of Default - PD, Weight of Evidence - WoE, Credit Scorecard scaling).
*   **Key Tech Stack**: Polars (high-performance tabular ETL), PyArrow, Scikit-Learn, LightGBM, Matplotlib, Seaborn.

---

## 2. Core Constraints (Must Obey)
1.  **Strict Gated Execution**: **DO NOT** proceed to the next phase or start writing code for a new phase without the user's explicit permission.
2.  **No Data Leakage**: Post-origination columns (e.g., `total_pymnt`, `recoveries`, `last_pymnt_d`) must be strictly excluded from preprocessing and training. Only use fields known at application time.
3.  **Target Definition**:
    *   Exclusion: Filter out `loan_status` = `'Current'`, `'In Grace Period'` or nulls (target is undefined).
    *   `Default (Y = 1)`: `'Charged Off'`, `'Default'`, `'Late (31-120 days)'`, `'Late (16-30 days)'`.
    *   `Non-Default (Y = 0)`: `'Fully Paid'`, and historical credit-policy compliant fully paid cases.
4.  **Chronological Validation Split**: Split training and testing sets based on the `issue_d` column to prevent temporal leakage and evaluate model performance on out-of-time (OOT) test data.
5.  **Scorecard Math**: Calibrate logistic regression log-odds using the Points-to-Double-the-Odds (PDO) formula.

---

## 3. Current State & Phase Tracker
The project is currently at:
*   **Active Phase**: **Phases 1 to 7** (COMPLETED).
*   **Next Action**: Handover complete. All deliverables, evaluation plots, scorecard scales, and unit tests are finalized.


For a detailed breakdown of all tasks, check [PROJECT_PROGRESS.md](file:///C:/Projects/Credit_Risk_Analysis/PROJECT_PROGRESS.md).

---

## 4. References & Documentation
*   Refer to [README.md](file:///C:/Projects/Credit_Risk_Analysis/README.md) for full explanations of mathematical formulas (PD, LGD, EAD, WoE, IV, and Points-to-Double-the-Odds scaling calculations).
*   Refer to [requirements.txt](file:///C:/Projects/Credit_Risk_Analysis/requirements.txt) for exact library versions.
