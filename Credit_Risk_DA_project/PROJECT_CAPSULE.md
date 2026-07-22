# Credit Risk Data Analysis & Forecasting Project Capsule

This capsule acts as the core memory for the Credit Risk Data Analysis & Forecasting project. It documents the target structure, data constraints, tech stack, and key findings.

---

## 1. Project Overview & Context
*   **Project Path**: `C:\Projects\Credit_Risk_Analysis\Credit_Risk_DA_project`
*   **Data Source**: `Source/processed_data.parquet` (pre-processed and cleaned credit dataset)
*   **Scope**: Descriptive data analysis, cohort (vintage) analysis of default rates, and time-series forecasting of loan volumes and default rates.
*   **Role Alignment**: Mid-Level Data Analyst (experiencing with SQL, Python, Polars, time-series forecasting, and BI).

---

## 2. Core Constraints
1.  **Strict Gated Folder**: All code, analysis scripts, plots, and tests must reside inside `Credit_Risk_DA_project/` folder.
2.  **No Machine Learning Models**: Focus strictly on statistics, SQL data aggregations, cohort tracking, and time-series forecasting.
3.  **Use Polars for Data Handling**: Leverages high-performance data manipulation via Polars, using `SQLContext` to execute SQL queries directly on Polars dataframes.

---

## 3. Technology Stack
*   **Data Processing**: Polars & Pandas
*   **SQL Engine**: Polars SQLContext
*   **Time-Series & Forecasting**: Scikit-Learn (Ridge Regression with seasonal and trend components for forecast stability), NumPy, and Pandas
*   **Visualization**: Matplotlib & Seaborn
*   **Testing**: Pytest

---

## 4. Operational Metrics
*   **Cohort Defaults**: Track default rate convergence across loan terms and origination vintages.
*   **Volume & Default Forecast**: Predict the next 12 months of credit demand and portfolio risk metrics.
