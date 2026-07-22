# Credit Risk Portfolio Data Analysis & Forecasting Project

This repository contains a data analysis and forecasting project built on historical lending data. It simulates the deliverables and workflow of a **Mid-Level Data Analyst**, focusing on business intelligence, portfolio cohort analysis, SQL-driven analytics, and statistical time-series forecasting.

---

## 📋 Executive Summary & Key Business Insights

1.  **DTI is a Critical Risk Driver**: A clear, monotonic relationship exists between Debt-to-Income (DTI) ratio and default rates. Borrowers with DTI > 30 default at nearly twice the rate (31.09%) of those with DTI < 10 (16.46%).
2.  **High-Risk Loan Purposes**: Small business loans carry the highest credit risk, with an ultimate default rate of **31.66%**, followed by renewable energy (25.16%) and moving (25.14%). Conversely, wedding (12.43%) and car (15.99%) loans are the safest.
3.  **Grade-Risk Calibration**: Average interest rates match credit grades perfectly (ranging from 7.09% for Grade A to 27.64% for Grade G). However, Grade G 60-month term loans experience a staggering **51.75% default rate**, suggesting that the pricing of these loans may not fully compensate for the underlying defaults.
4.  **12-Month Forecast Outlook**: The portfolio default rate is projected to remain stable but elevated around **24.5% to 26.0%** over the next 12 months, with loan volumes expected to hover around **21,000 to 24,000** loans per month.

---

## 🛠️ Project Structure

```
Credit_Risk_DA_project/
├── plots/                           # Saved visualization PNGs (300 DPI)
│   ├── default_rate_forecast.png
│   ├── dti_default_rates.png
│   ├── purpose_default_rates.png
│   ├── vintage_cohort_analysis.png
│   └── volume_forecast.png
├── results/                         # Aggregated data tables (CSV)
│   ├── dti_bucket_summary.csv
│   ├── monthly_forecasts.csv
│   ├── monthly_historical_metrics.csv
│   ├── portfolio_summary.csv
│   ├── purpose_summary.csv
│   └── vintage_cohort_summary.csv
├── PROJECT_CAPSULE.md               # Architecture and constraints memory
├── PROJECT_PROGRESS.md              # Project status and task tracker
├── README.md                        # Project documentation (this file)
├── data_analysis.py                 # SQL-driven portfolio and cohort analysis
├── forecasting.py                   # Time-series trend and seasonal forecasting
├── generate_charts.py               # Chart generation script
└── test_da_project.py               # Unit test suite
```

---

## 📊 Analytical Methodology & Findings

### 1. Portfolio Analysis by Grade and Term (`results/portfolio_summary.csv`)
Using SQL aggregations via **Polars SQLContext**, we analyzed loan performance:
*   **Grade A (36-month)**: 230,451 loans, average interest rate of **7.09%**, and a low default rate of **6.55%**.
*   **Grade G (60-month)**: 7,867 loans, average interest rate of **27.64%**, but a massive default rate of **51.75%**.
*   *Conclusion*: Longer term (60-month) loans exhibit significantly higher default rates across all credit grades compared to 36-month loans.

### 2. Vintage Cohort Analysis (`results/vintage_cohort_summary.csv`)
We grouped loans by their quarterly origination cohort (vintage) to analyze default trends over time:
*   Early vintages (2009-2013) maintained stable default rates between **12% and 17%**.
*   Later vintages (2016-2018) saw ultimate default rates climb, peaking near **29.5%** in Q2 2018. This suggests loosening credit standards or shifting economic conditions during this period.

### 3. Debt-to-Income (DTI) Analysis (`results/dti_bucket_summary.csv`)
Dividing borrowers into DTI buckets revealed a highly linear risk profile:
*   **DTI < 10**: 16.46% default rate.
*   **DTI 10-20**: 19.24% default rate.
*   **DTI 20-30**: 24.54% default rate.
*   **DTI >= 30**: 31.09% default rate.

---

## 📈 Time-Series Forecasting

The forecasting module (`forecasting.py`) aggregates historical data into monthly intervals and fits a **Ridge Regression Model** with:
1.  **Linear Time Trend ($t$)** to capture long-term expansion/contraction.
2.  **Monthly Seasonal Dummies** to capture monthly recurring seasonal behavior.

We project the next 12 months (representing 2019 data) with **95% Confidence Intervals** based on the residual standard error.

*   **Monthly Loan Volume Forecast**: Forecasts average around **22,000** loans/month, showing slight seasonal peaks in March and October.
*   **Default Rate Forecast**: Projections stay elevated around **25%**, highlighting the need for tighter underwriting parameters.

---

## 🚀 How to Run the Project

### 1. Requirements
Ensure you have the required packages installed:
```bash
pip install polars pandas numpy scikit-learn matplotlib seaborn pytest
```

### 2. Run Data Analysis
Executes the SQL queries on the processed parquet dataset and saves CSV outputs:
```bash
python Credit_Risk_DA_project/data_analysis.py
```

### 3. Run Forecasting
Aggregates time-series data, fits the forecasting model, and outputs predictions:
```bash
python Credit_Risk_DA_project/forecasting.py
```

### 4. Generate Visualizations
Generates clean, presentation-ready plots under the `plots/` directory:
```bash
python Credit_Risk_DA_project/generate_charts.py
```

### 5. Run Unit Tests
Runs pytest to verify that all statistical boundaries, DTI monotonicity, and format structures are correct:
```bash
python -m pytest Credit_Risk_DA_project/test_da_project.py
```
