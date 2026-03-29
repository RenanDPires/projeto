#!/usr/bin/env python3
"""
Exercise 01 - Sanity Test (Realistic Temperature Measurement Expectations)

Temperature-based loss measurements have inherent uncertainty due to:
- Heat transfer assumptions
- Thermal transient effects
- Environmental conditions
- Measurement accuracy limits

Target: Results within ±10% of temperature measurements
(±5% is ideal case; ±7-10% accounts for realistic measurement uncertainty)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.electromagnetics.biot_savart import calculate_loss_analytical


def run_realistic_sanity_test():
    """Run sanity test with realistic measurement uncertainty expectations."""
    
    reference_data = [
        {"current_a": 2000.0, "measurement": 64.50},
        {"current_a": 2250.0, "measurement": 73.70},
        {"current_a": 2500.0, "measurement": 94.60},
        {"current_a": 2800.0, "measurement": 119.30},
    ]
    
    default_input = get_default_exercise01_input()
    mu = default_input.material.mu
    sigma = default_input.material.sigma
    frequency_hz = default_input.frequency_hz
    thickness_m = default_input.plate.thickness_mm / 1000.0
    num_conductors = len(default_input.conductors)
    
    print("=" * 110)
    print("EXERCISE 01 — SANITY TEST vs TEMPERATURE MEASUREMENTS")
    print("=" * 110)
    print(f"\nMaterial: Aço Transformador | Frequency: {frequency_hz}Hz | Plate: {default_input.plate.width_mm}×{default_input.plate.height_mm}×{thickness_m*1000}mm")
    print()
    
    print(f"{'Current':<10} {'Calculated':<14} {'Measured':<14} {'Error %':<12} {'Status ±5%':<12} {'Status ±10%':<12}")
    print("-" * 110)
    
    errors = []
    pass_5pct = 0
    pass_10pct = 0
    
    for test_case in reference_data:
        current_a = test_case["current_a"]
        measurement = test_case["measurement"]
        
        computed = calculate_loss_analytical(
            im=current_a,
            thickness_m=thickness_m,
            frequency_hz=frequency_hz,
            mu=mu,
            sigma=sigma,
            num_conductors=num_conductors,
        )
        
        error_pct = abs(computed - measurement) / measurement * 100.0
        errors.append(error_pct)
        
        within_5pct = error_pct <= 5.0
        within_10pct = error_pct <= 10.0
        
        if within_5pct:
            pass_5pct += 1
            status_5pct = "✅ YES"
        else:
            status_5pct = "❌ NO" if not within_10pct else "⚠️  NEAR"
        
        if within_10pct:
            pass_10pct += 1
            status_10pct = "✅ YES"
        else:
            status_10pct = "❌ NO"
        
        print(f"{current_a:>7.0f}A   {computed:>12.2f}W   {measurement:>12.2f}W   {error_pct:>9.2f}%    {status_5pct:<12} {status_10pct:<12}")
    
    print()
    print("=" * 110)
    print("SUMMARY")
    print("=" * 110)
    
    avg_error = sum(errors) / len(errors)
    max_error = max(errors)
    
    print(f"Average Error: {avg_error:.2f}%")
    print(f"Maximum Error: {max_error:.2f}%")
    print(f"Tests Within ±5%: {pass_5pct}/{len(errors)} ({pass_5pct/len(errors)*100:.0f}%)")
    print(f"Tests Within ±10%: {pass_10pct}/{len(errors)} ({pass_10pct/len(errors)*100:.0f}%)")
    print()
    
    success = True
    
    if pass_5pct >= 3:  # 75% or more
        print("✅ STRONG RESULTS: ≥75% of measurements within ±5%")
    elif pass_5pct >= 2: # 50% or more
        print("⚠️  ACCEPTABLE: ≥50% within ±5%, but check quality")
    else:
        print("❌ WEAK RESULTS: <50% within ±5%")
        success = False
    
    if avg_error <= 7.0:
        print("✅ GOOD AVERAGE: Mean error ≤7%")
    else:
        print("⚠️  Higher average error suggests possible systematic bias")
    
    if pass_10pct == len(errors):
        print("✅ CONFIDENCE: 100% of results within ±10% uncertainty band")
    else:
        print(f"⚠️  WARNING: {len(errors) - pass_10pct} results exceed ±10% tolerance")
        success = False
    
    return success


if __name__ == "__main__":
    success = run_realistic_sanity_test()
    sys.exit(0 if success else 1)
