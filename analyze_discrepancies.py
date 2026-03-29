#!/usr/bin/env python3
"""
Analyze the differences between analytical formula and temperature measurements.
Find if there's a systematic calibration factor needed.
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.electromagnetics.biot_savart import calculate_loss_analytical


def analyze_discrepancies():
    """Analyze the pattern of differences between formula and measurements."""
    
    reference_data = [
        {"current_a": 2000.0, "table_analytical": 63.79, "measurement": 64.50},
        {"current_a": 2250.0, "table_analytical": 80.74, "measurement": 73.70},
        {"current_a": 2500.0, "table_analytical": 99.67, "measurement": 94.60},
        {"current_a": 2800.0, "table_analytical": 125.00, "measurement": 119.30},
    ]
    
    default_input = get_default_exercise01_input()
    mu = default_input.material.mu
    sigma = default_input.material.sigma
    frequency_hz = default_input.frequency_hz
    thickness_m = default_input.plate.thickness_mm / 1000.0
    num_conductors = len(default_input.conductors)
    
    print("=" * 100)
    print("DISCREPANCY ANALYSIS")
    print("=" * 100)
    print()
    print(f"{'Current':<10} {'Computed':<12} {'Table':<12} {'Measur.':<12} {'vs Table':<12} {'vs Measur.':<12} {'Ratio':<10}")
    print("-" * 100)
    
    ratios_table = []
    ratios_measurement = []
    
    for test_case in reference_data:
        current_a = test_case["current_a"]
        table_analytical = test_case["table_analytical"]
        measurement = test_case["measurement"]
        
        computed = calculate_loss_analytical(
            im=current_a,
            thickness_m=thickness_m,
            frequency_hz=frequency_hz,
            mu=mu,
            sigma=sigma,
            num_conductors=num_conductors,
        )
        
        error_vs_table = (computed - table_analytical) / table_analytical * 100.0
        error_vs_measurement = (computed - measurement) / measurement * 100.0
        ratio = measurement / computed
        
        ratios_table.append((computed - table_analytical) / computed)
        ratios_measurement.append(ratio)
        
        print(f"{current_a:>7.0f}A   {computed:>10.2f}    {table_analytical:>10.2f}    {measurement:>10.2f}    "
              f"{error_vs_table:>9.2f}%    {error_vs_measurement:>9.2f}%    {ratio:>8.4f}")
    
    print()
    print("ANALYSIS:")
    print(f"  Average Measurement/Computed Ratio: {np.mean(ratios_measurement):.4f}")
    print(f"  Std Dev of Ratio: {np.std(ratios_measurement):.4f}")
    print()
    
    # Check if there's a consistent calibration factor
    if np.std(ratios_measurement) < 0.02:
        calib_factor = np.mean(ratios_measurement)
        print(f"  ℹ️  Consistent systematic difference detected")
        print(f"  Suggested calibration adjustment: multiply by {calib_factor:.4f}")
        print(f"  This would give measurement accuracy")
    else:
        print(f"  ℹ️  Non-systematic differences (high std dev)")
        print(f"  Different currents show different error patterns")
    
    # Alternative: check if table values vs measurement have a pattern
    print()
    print("TABLE vs MEASUREMENT ANALYSIS:")
    table_ratios = [test_case["measurement"] / test_case["table_analytical"] for test_case in reference_data]
    print(f"  Measurement/Table Ratios: {[f'{r:.4f}' for r in table_ratios]}")
    print(f"  Mean: {np.mean(table_ratios):.4f}, Std: {np.std(table_ratios):.4f}")


if __name__ == "__main__":
    analyze_discrepancies()
