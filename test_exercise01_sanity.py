#!/usr/bin/env python3
"""
Exercise 01 - Final Sanity Test

Compare analytical results against steady-state temperature measurement data.
Tolerance: ±5% maximum error.

Reference Data (Temperature Measurement Method - Steady State):
Corrente (A) | Cálculo Analítico (W) | Medição Temperatura (W) | Banda (±5%)
2000         | 63.79                | 64.50                  | 60.6 - 67.7
2250         | 80.74                | 73.70                  | 70.0 - 77.4
2500         | 99.67                | 94.60                  | 89.9 - 99.3
2800         | 125.00               | 119.30                 | 113.3 - 125.3
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.schemas.inputs import Exercise01Input, ConductorInput, MaterialInput, PlateInput, MeshInput, HoleInput
from app.core.electromagnetics.biot_savart import calculate_loss_analytical


def run_sanity_test():
    """Run final sanity test against temperature measurement data."""
    
    # Reference data: corrente, expected_analytical, medição_temperatura
    reference_data = [
        {"current_a": 2000.0, "expected_analytical": 63.79, "measurement": 64.50},
        {"current_a": 2250.0, "expected_analytical": 80.74, "measurement": 73.70},
        {"current_a": 2500.0, "expected_analytical": 99.67, "measurement": 94.60},
        {"current_a": 2800.0, "expected_analytical": 125.00, "measurement": 119.30},
    ]
    
    # Get default configuration (transformer steel, 60Hz)
    default_input = get_default_exercise01_input()
    
    # Extract material properties
    mu = default_input.material.mu
    sigma = default_input.material.sigma
    frequency_hz = default_input.frequency_hz
    thickness_m = default_input.plate.thickness_mm / 1000.0
    num_conductors = len(default_input.conductors)
    
    print("=" * 100)
    print("EXERCISE 01 — FINAL SANITY TEST")
    print("Analytical Calculation vs Temperature Measurement (Steady State)")
    print("=" * 100)
    print(f"\nConfiguration:")
    print(f"  Material: Aço Transformador")
    print(f"  μ = {mu:.6e} H/m")
    print(f"  σ = {sigma:.6e} S/m")
    print(f"  Frequency: {frequency_hz} Hz")
    print(f"  Plate: {default_input.plate.width_mm}×{default_input.plate.height_mm}×{thickness_m*1000:.1f}mm")
    print(f"  Conductors: {num_conductors}")
    print(f"  Tolerance: ±5.0%")
    print()
    
    # Test each current value
    all_passed = True
    results = []
    
    print(f"{'Current':<10} {'Analytical':<12} {'Measurement':<12} {'vs Measur.':<12} {'Band ±5%':<15} {'Status':<10}")
    print("-" * 100)
    
    for test_case in reference_data:
        current_a = test_case["current_a"]
        expected_analytical = test_case["expected_analytical"]
        measurement = test_case["measurement"]
        tolerance_pct = 5.0
        
        # Calculate analytical loss with current method
        computed_analytical = calculate_loss_analytical(
            im=current_a,
            thickness_m=thickness_m,
            frequency_hz=frequency_hz,
            mu=mu,
            sigma=sigma,
            num_conductors=num_conductors,
        )
        
        # Compare computed analytical vs expected analytical (sanity check)
        analytical_error_pct = abs(computed_analytical - expected_analytical) / expected_analytical * 100.0
        
        # Compare computed analytical vs measurement (main test)
        measurement_error_pct = abs(computed_analytical - measurement) / measurement * 100.0
        
        # Check tolerance against measurement
        band_min = measurement * (1 - tolerance_pct / 100.0)
        band_max = measurement * (1 + tolerance_pct / 100.0)
        is_passing = band_min <= computed_analytical <= band_max
        status = "✅ PASS" if is_passing else "❌ FAIL"
        
        results.append({
            "current": current_a,
            "analytical": computed_analytical,
            "measurement": measurement,
            "error": measurement_error_pct,
            "status": is_passing,
        })
        
        if not is_passing:
            all_passed = False
        
        band_str = f"{band_min:.2f}-{band_max:.2f}W"
        print(f"{current_a:>7.0f}A   {computed_analytical:>10.2f}W   {measurement:>10.2f}W   "
              f"{measurement_error_pct:>9.2f}%      {band_str:<15} {status}")
    
    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    # Statistics
    errors = [r["error"] for r in results]
    avg_error = sum(errors) / len(errors)
    max_error = max(errors)
    min_error = min(errors)
    
    print(f"Average Error vs Measurement: {avg_error:.3f}%")
    print(f"Maximum Error: {max_error:.3f}%")
    print(f"Minimum Error: {min_error:.3f}%")
    print(f"Tolerance: ±5.0%")
    print()
    
    if all_passed:
        print("✅ ALL TESTS PASSED - Exercise 01 Validated Against Temperature Measurements")
        return True
    else:
        print("❌ SOME TESTS FAILED - Analytical results outside ±5% tolerance band")
        return False


if __name__ == "__main__":
    success = run_sanity_test()
    sys.exit(0 if success else 1)
