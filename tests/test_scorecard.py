import os
import sys
import numpy as np
import pytest
import polars as pl

# Add workspace directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import TARGET_MAPPING
from src.scorecard import calculate_scaling_parameters, calculate_scores

def test_scaling_parameters():
    """Verify Points-to-Double-the-Odds scaling factor and offset calculation."""
    factor, offset = calculate_scaling_parameters()
    
    # Mathematical values:
    # Factor = 20 / ln(2) approx 28.8539
    # Offset = 600 - Factor * ln(50) approx 487.1229
    assert np.isclose(factor, 28.8539008)
    assert np.isclose(offset, 487.1228512)

def test_target_mapping():
    """Verify target mapping definitions."""
    assert TARGET_MAPPING["Fully Paid"] == 0
    assert TARGET_MAPPING["Charged Off"] == 1
    assert TARGET_MAPPING["Late (31-120 days)"] == 1
    assert TARGET_MAPPING["Late (16-30 days)"] == 1
    assert TARGET_MAPPING["Default"] == 1

def test_scorecard_score_calculation():
    """Verify calculate_scores correctly assigns points based on rules."""
    # Build a simple mock rule set
    rules = {
        "selected_features": ["fico_range_low", "verification_status"],
        "binner_rules": {
            "fico_range_low": {
                "type": "numeric",
                "edges": [500.0, 600.0, 700.0, 800.0]
            },
            "verification_status": {
                "type": "categorical",
                "keep_categories": ["Verified", "Not Verified"]
            }
        }
    }
    
    # Points assignment
    # numeric fico_range_low bins: 0 (Missing), 1 (<=600), 2 ((600,700]), 3 ((700,800]), 4 (>800)
    # categorical verification_status bins: "Missing", "Verified", "Not Verified", "Other"
    scorecard_points = {
        "fico_range_low": {
            "0": 10,
            "1": 20,
            "2": 40,
            "3": 60,
            "4": 80
        },
        "verification_status": {
            "Missing": 5,
            "Verified": 15,
            "Not Verified": 30,
            "Other": 25
        }
    }
    
    # Dummy dataset
    df = pl.DataFrame({
        "fico_range_low": [550.0, 750.0, None],
        "verification_status": ["Verified", "Not Verified", "Source Verified"] # Source Verified should fall back to 'Other'
    })
    
    # Expected points:
    # Row 1: fico=550 (<=600 -> bin 1 -> 20 pts) + verification="Verified" (15 pts) = 35 pts
    # Row 2: fico=750 ((700,800] -> bin 3 -> 60 pts) + verification="Not Verified" (30 pts) = 90 pts
    # Row 3: fico=None (Missing -> bin 0 -> 10 pts) + verification="Source Verified" (Other -> 25 pts) = 35 pts
    
    scores = calculate_scores(df, scorecard_points, rules)
    assert scores[0] == 35
    assert scores[1] == 90
    assert scores[2] == 35
