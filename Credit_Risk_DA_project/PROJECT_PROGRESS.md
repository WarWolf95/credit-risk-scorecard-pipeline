# Project Progress Tracker (DA Project)

This document tracks the progress of the Credit Risk Data Analysis & Forecasting project. Steps are marked as:
*   `[ ]` Not Started
*   `[/]` In Progress
*   `[x]` Completed

---

## Progress Summary

### [x] Phase 1: Set Up & Initialization
*   [x] Create folder `Credit_Risk_DA_project`
*   [x] Create `PROJECT_CAPSULE.md`
*   [x] Create `PROJECT_PROGRESS.md` (this file)

### [x] Phase 2: SQL-Based Portfolio & Cohort Analysis
*   [x] Write `data_analysis.py` utilizing Polars SQLContext
*   [x] Calculate loan characteristics by grade, sub-grade, and term
*   [x] Perform quarterly vintage cohort analysis of default rates
*   [x] Analyze correlation of default rates with debt-to-income (DTI) and purpose

### [x] Phase 3: Time-Series Forecasting
*   [x] Write `forecasting.py` to aggregate monthly loan stats
*   [x] Implement OLS/Ridge trend-seasonal regression model for forecasting
*   [x] Forecast monthly default rates and loan volumes for next 12 months with 95% CI

### [x] Phase 4: Visualization and Reporting
*   [x] Write `generate_charts.py` to plot cohort curves, metrics, and forecasts
*   [x] Generate professional charts to `plots/` folder
*   [x] Write comprehensive final analysis report in `README.md`

### [x] Phase 5: Verification and Testing
*   [x] Write unit tests in `test_da_project.py`
*   [x] Run pytest to verify all analytical calculations and forecasting functions
