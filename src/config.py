import os
from pathlib import Path

# Base paths — resolved dynamically so the project is portable
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
RAW_DATA_PATH = os.path.join(PROJECT_DIR, "Source", "accepted_2007_to_2018Q4.csv")
PROCESSED_DATA_PATH = os.path.join(PROJECT_DIR, "Source", "processed_data.parquet")

# Column Configurations
TARGET_COL = "target"
DATE_COL = "issue_d"

# Columns to keep (known at application time)
APPLICATION_COLS = [
    "loan_amnt",
    "term",
    "int_rate",
    "installment",
    "grade",
    "sub_grade",
    "emp_length",
    "home_ownership",
    "annual_inc",
    "verification_status",
    "purpose",
    "dti",
    "delinq_2yrs",
    "earliest_cr_line",
    "fico_range_low",
    "fico_range_high",
    "open_acc",
    "pub_rec",
    "revol_bal",
    "revol_util",
    "total_acc",
    "initial_list_status",
    "collections_12_mths_ex_med",
    "pub_rec_bankruptcies",
    "tax_liens",
    "tot_cur_bal",
    "total_rev_hi_lim",
    "acc_open_past_24mths",
    "pct_tl_nvr_dlq",
    "percent_bc_gt_75"
]

# Target mapping rules
# 1 = Default/Charged Off, 0 = Fully Paid
# Excluded statuses will be filtered out.
TARGET_MAPPING = {
    # Non-Default (Y = 0)
    "Fully Paid": 0,
    "Does not meet the credit policy. Status:Fully Paid": 0,
    
    # Default (Y = 1)
    "Charged Off": 1,
    "Default": 1,
    "Late (31-120 days)": 1,
    "Late (16-30 days)": 1,
    "Does not meet the credit policy. Status:Charged Off": 1,
}

# Excluded statuses (all other statuses like Current, In Grace Period, or nulls are excluded)
EXCLUDED_STATUSES = [
    "Current",
    "In Grace Period",
    None,
    ""
]
