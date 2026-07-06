# Credit Risk Analysis & Scorecard Modeling

This repository contains a production-grade implementation of a Credit Risk modeling pipeline using the LendingClub dataset (2007-2018Q4). The project is structured to demonstrate data preprocessing, feature engineering (including Weight of Evidence binning), model development, performance evaluation, and traditional credit scorecard construction.

---

## 1. Credit Risk Fundamentals

Credit risk represents the possibility of a loss resulting from a borrower's failure to repay a loan or meet contractual obligations. In retail banking and consumer lending, risk is quantified using three primary parameters to estimate **Expected Loss (EL)**:

$$\text{Expected Loss (EL)} = \text{PD} \times \text{LGD} \times \text{EAD}$$

### A. Probability of Default (PD)
*   **Definition**: The likelihood that a borrower will default on their debt obligation within a given time horizon (typically 12 months).
*   **Value**: Range $[0, 1]$ or $[0\%, 100\%]$.
*   **Modeling Approach**: Binary classification (Logistic Regression, Gradient Boosted Trees like LightGBM) predicting whether a borrower defaults ($Y=1$) or pays back ($Y=0$). This project focuses heavily on PD modeling.

### B. Loss Given Default (LGD)
*   **Definition**: The percentage of the exposure that is lost if the borrower defaults, after accounting for any recoveries (selling collateral, debt collection).
*   **Formula**: $\text{LGD} = 1 - \text{Recovery Rate}$.
*   **Value**: Range $[0, 1]$ (or sometimes $>1$ if recovery costs are extremely high).
*   **Modeling Approach**: Beta regression, linear regression, or tree-based regression on the subset of defaulted loans.

### C. Exposure at Default (EAD)
*   **Definition**: The total outstanding dollar value of the loan at the moment the borrower defaults.
*   **Modeling Approach**: For term loans, this is usually the outstanding principal. For revolving credit (credit cards), EAD includes the drawn balance plus a percentage of the undrawn credit line (Credit Conversion Factor).

---

## 2. Model Methodology: Scorecard vs Machine Learning

In retail credit risk, two approaches dominate:

| Feature | Credit Scorecard (Logistic Regression + WoE) | Machine Learning (LightGBM / XGBoost) |
| :--- | :--- | :--- |
| **Interpretability** | **Extreme**. Decisions can be broken down to individual points. | **Low (Black Box)**. Requires SHAP/LIME for explanation. |
| **Regulatory Compliance** | High compliance. Complies easily with Adverse Action requirements. | Lower compliance. Harder to satisfy audit requirements. |
| **Performance** | Good. Relies on linear assumptions per bin. | **Excellent**. Captures non-linear relationships/interactions. |

We implement **both** in this project:
1.  **LightGBM** to set the upper bound of predictive performance.
2.  **Logistic Regression with Weight of Evidence (WoE) binning** to build a traditional, production-ready credit scorecard.

---

## 3. Weight of Evidence (WoE) & Information Value (IV)

Before training the Logistic Regression model, variables are binned, and each bin is encoded with its **Weight of Evidence (WoE)**.

### Weight of Evidence (WoE)
WoE measures the relative risk of a specific attribute (bin) compared to the overall population. It is calculated as:

$$\text{WoE}_i = \ln \left( \frac{\text{Prop. Good}_i}{\text{Prop. Bad}_i} \right)$$

*   **Positive WoE**: The bin contains a higher proportion of "Good" (non-defaulting) accounts than "Bad" accounts. It indicates lower risk.
*   **Negative WoE**: The bin has a higher proportion of "Bad" accounts than "Good" accounts. It indicates higher risk.

### Information Value (IV)
IV is a metric used to rank variables by their predictive power for feature selection:

$$\text{IV} = \sum_{i=1}^{n} \left( \text{Prop. Good}_i - \text{Prop. Bad}_i \right) \times \text{WoE}_i$$

**IV Interpretation Rules of Thumb:**
*   $< 0.02$: Useless for prediction
*   $0.02 \text{ to } 0.1$: Weak predictive power
*   $0.1 \text{ to } 0.3$: Medium predictive power
*   $0.3 \text{ to } 0.5$: Strong predictive power
*   $> 0.5$: Suspiciously high (often indicates data leakage)

---

## 4. Scorecard Scaling (Points to Double the Odds)

To convert Logistic Regression probabilities into an integer-based Credit Scorecard (like a FICO score), we map log-odds to points.
The score is calculated as a linear transformation of the log-odds:

$$\text{Score} = \text{Offset} + \text{Factor} \times \ln(\text{Odds})$$

Where $\text{Odds} = \frac{P(\text{Good})}{P(\text{Bad})} = \frac{1 - \text{PD}}{\text{PD}}$.

We define scaling constraints:
1.  **Base Score**: A specific score (e.g., $600$ points) represents a specific odds ratio (e.g., $50:1$ odds of being Good).
2.  **Points to Double the Odds (PDO)**: The number of score points required to double the odds. (e.g., if PDO = $20$, a score increase from $600$ to $620$ shifts the odds from $50:1$ to $100:1$).

The equations to solve for `Factor` and `Offset` are:

$$\text{Factor} = \frac{\text{PDO}}{\ln(2)}$$

$$\text{Offset} = \text{Base Score} - \text{Factor} \times \ln(\text{Base Odds})$$

Using these, we assign a point value to each feature bin based on its WoE value and the model coefficient:

$$\text{Points}_i = \left( -\beta_j \times \text{WoE}_i - \frac{\alpha}{N} \right) \times \text{Factor} + \frac{\text{Offset}}{N}$$

Where $\beta_j$ is the coefficient for feature $j$, $\alpha$ is the intercept, and $N$ is the number of features. Note that the negative signs correct for the model predicting probability of default ($Y=1$), ensuring that higher scorecard points correspond to lower default risk (i.e. "Good" credit).

---

## 5. Crucial Industry Constraints & Avoidance of Data Leakage

In credit risk projects, a common mistake is using **post-origination variables** in modeling. At the time a customer applies for a loan, we do not know their payment behavior.
We strictly separate the columns:

*   **Application-Time Columns (Keep)**: `loan_amnt`, `term`, `emp_length`, `home_ownership`, `annual_inc`, `verification_status`, `dti`, `delinq_2yrs`, `fico_range_low`, `fico_range_high`, `open_acc`, `pub_rec`, etc.
*   **Post-Origination Columns (Drop)**: `total_pymnt`, `last_pymnt_amnt`, `recoveries`, `collection_recovery_fee`, `next_pymnt_d`. If these are in the dataset, the model will cheat by knowing who already paid back or went to collection.

---

## 6. Directory Structure
*   `src/`: Modules for ETL, feature engineering, modeling, and scaling.
*   `tests/`: Unit tests for validation scripts.
*   `plots/`: Evaluation visualizations.
*   `PROJECT_PROGRESS.md`: Steps completed and pending.
*   `PROJECT_CAPSULE.md`: Cross-agent context synchronization state file.
